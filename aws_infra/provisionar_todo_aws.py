"""
Script Maestro de Aprovisionamiento Automatizado en AWS para PetCare (Evaluación N.º 4).
Crea y configura todos los servicios separados exigidos en el diagrama de arquitectura:
1. Bucket Amazon S3 con cifrado SSE-S3 (AES256), Block Public Access, Versionado y subida de estáticos/PDFs.
2. Segunda Instancia EC2 separada (EC2 - FRONTEND) conectada al Backend / API Gateway.
3. Instancia Amazon RDS PostgreSQL separada con cifrado KMS en reposo, respaldos automáticos (7 días)
   y Security Group restringido exclusivamente al puerto TCP 5432 desde la EC2 Backend.
4. Amazon API Gateway (REST API) integrando el Backend Django con Rate Limit (Rate: 2 req/s, Burst: 5).
5. Tópico Amazon SNS + Alarma en Amazon CloudWatch (CPUUtilization >= 70% en la EC2 Backend).
6. Función AWS Lambda + Regla Amazon EventBridge Scheduler (rate(7 hours)) para respaldos cada 7 horas.
"""
import io
import json
import os
import time
import zipfile
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
BACKEND_PUBLIC_IP = '98.85.49.169'
BACKEND_DOMAIN = 'https://petcaree.duckdns.org'
RDS_INSTANCE_ID = 'petcare-rds-postgres'
RDS_DB_NAME = 'petcare_db'
RDS_MASTER_USER = 'postgres'
RDS_MASTER_PASS = os.environ.get('RDS_MASTER_PASS', 'PetCareRDS2026!')


def get_session():
    return boto3.Session(region_name=REGION)


def step_1_s3_bucket(session, account_id: str) -> dict:
    s3 = session.client('s3')
    bucket_name = f"petcare-eva4-static-media-{account_id}"
    print(f"\n[1/6] Configurando Bucket Amazon S3: {bucket_name}...")

    try:
        if REGION == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': REGION},
            )
    except ClientError as e:
        if e.response['Error']['Code'] not in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            raise

    # 1. Activar Block Public Access (Actividad 6)
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True,
        },
    )

    # 2. Activar Cifrado en Reposo SSE-S3 (AES256)
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'},
                    'BucketKeyEnabled': True,
                }
            ]
        },
    )

    # 3. Activar Versionado del Bucket
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'},
    )

    # 4. Subir archivos estáticos y receta PDF de demostración cifrados con AES256
    pdf_demo = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 118 >> stream\n"
        b"BT /F1 14 Tf 50 720 Td (PETCARE CLINICA VETERINARIA - RECETA MEDICA DIGITAL) Tj "
        b"0 -25 Td (Paciente: Thor - Tutor: Carlos Mendoza - Dr. Camila Soto) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \ntrailer << /Root 1 0 R /Size 5 >>\n%%EOF"
    )
    s3.put_object(
        Bucket=bucket_name,
        Key='recetas/receta_ficha_clinica_thor_2026.pdf',
        Body=pdf_demo,
        ContentType='application/pdf',
        ServerSideEncryption='AES256',
    )
    s3.put_object(
        Bucket=bucket_name,
        Key='static/css/petcare_eva4.css',
        Body=b"/* Estilos estaticos PetCare EVA 4 servidos desde Amazon S3 (SSE-S3) */\nbody { background: #f8fafc; }\n",
        ContentType='text/css',
        ServerSideEncryption='AES256',
    )

    presigned = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': 'recetas/receta_ficha_clinica_thor_2026.pdf'},
        ExpiresIn=900,
    )
    print(f"  -> Bucket S3 listo con SSE-S3, Block Public Access y Versionado.")
    return {'bucket_name': bucket_name, 'sample_presigned_url': presigned}


def step_2_discover_backend_and_launch_frontend_ec2(session) -> dict:
    ec2 = session.client('ec2')
    print("\n[2/6] Inspeccionando EC2 Backend y creando 2.ª Instancia separada (EC2 - FRONTEND)...")

    res = ec2.describe_instances(
        Filters=[{'Name': 'ip-address', 'Values': [BACKEND_PUBLIC_IP]}]
    )
    instances = [i for r in res.get('Reservations', []) for i in r.get('Instances', [])]
    if not instances:
        res = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        instances = [i for r in res.get('Reservations', []) for i in r.get('Instances', [])]

    backend_inst = instances[0]
    backend_id = backend_inst['InstanceId']
    vpc_id = backend_inst['VpcId']
    subnet_id = backend_inst['SubnetId']
    ami_id = backend_inst['ImageId']
    key_name = backend_inst.get('KeyName')
    inst_type = backend_inst.get('InstanceType', 't2.micro')
    backend_sg_id = backend_inst['SecurityGroups'][0]['GroupId']
    backend_private_ip = backend_inst.get('PrivateIpAddress')

    # Asegurar que la EC2 Backend tenga nombre claro
    ec2.create_tags(
        Resources=[backend_id],
        Tags=[{'Key': 'Name', 'Value': 'eva4_petcare_BACKEND_DRF'}],
    )

    # Crear o reutilizar Security Group para EC2 Frontend
    fe_sg_name = 'petcare-eva4-frontend-sg'
    sgs = ec2.describe_security_groups(
        Filters=[{'Name': 'group-name', 'Values': [fe_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc_id]}]
    ).get('SecurityGroups', [])
    if sgs:
        fe_sg_id = sgs[0]['GroupId']
    else:
        fe_sg_id = ec2.create_security_group(
            GroupName=fe_sg_name,
            Description='Security Group para instancia EC2 Frontend de PetCare EVA 4',
            VpcId=vpc_id,
        )['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=fe_sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            ],
        )

    # Verificar si ya existe la instancia EC2 Frontend
    existing_fe = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['eva4_petcare_FRONTEND']},
            {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
        ]
    )
    fe_list = [i for r in existing_fe.get('Reservations', []) for i in r.get('Instances', [])]

    if fe_list:
        fe_inst = fe_list[0]
        fe_id = fe_inst['InstanceId']
    else:
        user_data_script = f"""#!/bin/bash
curl -sSL https://raw.githubusercontent.com/Eduarts-00/eva4_backend_petcare/main/deploy_frontend_ec2.sh | sudo bash -s -- {BACKEND_DOMAIN}
"""
        run_args = {
            'ImageId': ami_id,
            'InstanceType': inst_type,
            'MinCount': 1,
            'MaxCount': 1,
            'NetworkInterfaces': [
                {
                    'DeviceIndex': 0,
                    'SubnetId': subnet_id,
                    'Groups': [fe_sg_id],
                    'AssociatePublicIpAddress': True,
                }
            ],
            'UserData': user_data_script,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': 'eva4_petcare_FRONTEND'}],
                }
            ],
        }
        if key_name:
            run_args['KeyName'] = key_name
        launched = ec2.run_instances(**run_args)
        fe_id = launched['Instances'][0]['InstanceId']

    print(f"  -> EC2 Backend ID : {backend_id} ({BACKEND_PUBLIC_IP})")
    print(f"  -> EC2 Frontend ID: {fe_id}")
    return {
        'backend_instance_id': backend_id,
        'backend_sg_id': backend_sg_id,
        'backend_private_ip': backend_private_ip,
        'vpc_id': vpc_id,
        'frontend_instance_id': fe_id,
        'frontend_sg_id': fe_sg_id,
    }


def step_3_rds_postgresql(session, vpc_id: str, backend_sg_id: str) -> dict:
    ec2 = session.client('ec2')
    rds = session.client('rds')
    print("\n[3/6] Configurando Security Group puerto 5432 e Instancia Amazon RDS PostgreSQL...")

    rds_sg_name = 'petcare-eva4-rds-postgres-sg'
    sgs = ec2.describe_security_groups(
        Filters=[{'Name': 'group-name', 'Values': [rds_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc_id]}]
    ).get('SecurityGroups', [])
    if sgs:
        rds_sg_id = sgs[0]['GroupId']
    else:
        rds_sg_id = ec2.create_security_group(
            GroupName=rds_sg_name,
            Description='Restringe acceso TCP 5432 exclusivamente al Security Group de EC2 Backend PetCare',
            VpcId=vpc_id,
        )['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=rds_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 5432,
                    'ToPort': 5432,
                    'UserIdGroupPairs': [
                        {
                            'GroupId': backend_sg_id,
                            'Description': 'Acceso exclusivo desde EC2 Backend Django REST Framework',
                        }
                    ],
                }
            ],
        )

    # Verificar si ya existe la instancia RDS
    try:
        db_info = rds.describe_db_instances(DBInstanceIdentifier=RDS_INSTANCE_ID)['DBInstances'][0]
        status_rds = db_info['DBInstanceStatus']
        print(f"  -> Instancia RDS '{RDS_INSTANCE_ID}' ya existe (estado: {status_rds}).")
    except ClientError:
        print(f"  -> Creando nueva instancia RDS PostgreSQL '{RDS_INSTANCE_ID}' con cifrado KMS en reposo...")
        created = rds.create_db_instance(
            DBName=RDS_DB_NAME,
            DBInstanceIdentifier=RDS_INSTANCE_ID,
            AllocatedStorage=20,
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            MasterUsername=RDS_MASTER_USER,
            MasterUserPassword=RDS_MASTER_PASS,
            VpcSecurityGroupIds=[rds_sg_id],
            BackupRetentionPeriod=7,
            PreferredBackupWindow='04:00-04:30',
            PreferredMaintenanceWindow='sun:05:00-sun:05:30',
            MultiAZ=False,
            PubliclyAccessible=False,
            StorageType='gp2',
            StorageEncrypted=True,
            DeletionProtection=False,
            Tags=[{'Key': 'Name', 'Value': 'PetCare-EVA4-RDS-PostgreSQL'}],
        )
        db_info = created['DBInstance']

    endpoint = db_info.get('Endpoint', {}).get('Address', 'creando-en-progreso.rds.amazonaws.com')
    return {
        'rds_instance_id': RDS_INSTANCE_ID,
        'rds_sg_id': rds_sg_id,
        'rds_status': db_info.get('DBInstanceStatus'),
        'rds_endpoint': endpoint,
        'storage_encrypted': db_info.get('StorageEncrypted', True),
        'backup_retention_days': db_info.get('BackupRetentionPeriod', 7),
    }


def step_4_api_gateway_with_rate_limit(session) -> dict:
    apigw = session.client('apigateway')
    print("\n[4/6] Configurando Amazon API Gateway (REST API) con Rate Limit (Rate: 2 req/s, Burst: 5)...")

    api_name = 'PetCare-EVA4-API-Gateway'
    existing = apigw.get_rest_apis().get('items', [])
    api_obj = next((a for a in existing if a['name'] == api_name), None)

    if not api_obj:
        api_obj = apigw.create_rest_api(
            name=api_name,
            description='API Gateway para PetCare EVA 4 con Throttling / Rate Limiting hacia EC2 Backend DRF',
            endpointConfiguration={'types': ['REGIONAL']},
        )
    api_id = api_obj['id']

    resources = apigw.get_resources(restApiId=api_id)['items']
    root_res = next(r for r in resources if r['path'] == '/')
    proxy_res = next((r for r in resources if r.get('pathPart') == '{proxy+}'), None)

    if not proxy_res:
        proxy_res = apigw.create_resource(
            restApiId=api_id,
            parentId=root_res['id'],
            pathPart='{proxy+}',
        )

    # Configurar método ANY en / y /{proxy+} hacia https://petcaree.duckdns.org
    for res_id, uri_target, req_params, int_params in [
        (root_res['id'], f"{BACKEND_DOMAIN}/", {}, {}),
        (
            proxy_res['id'],
            f"{BACKEND_DOMAIN}/{{proxy}}",
            {'method.request.path.proxy': True},
            {'integration.request.path.proxy': 'method.request.path.proxy'},
        ),
    ]:
        try:
            apigw.put_method(
                restApiId=api_id,
                resourceId=res_id,
                httpMethod='ANY',
                authorizationType='NONE',
                requestParameters=req_params,
            )
        except ClientError:
            pass

        apigw.put_integration(
            restApiId=api_id,
            resourceId=res_id,
            httpMethod='ANY',
            type='HTTP_PROXY',
            integrationHttpMethod='ANY',
            uri=uri_target,
            requestParameters=int_params,
        )

    # Desplegar al stage 'prod' y aplicar Stage Throttling (Rate: 2 req/s, Burst: 5)
    apigw.create_deployment(
        restApiId=api_id,
        stageName='prod',
        description='Despliegue EVA 4 con Rate Limit (Rate 2 req/s, Burst 5)',
    )
    apigw.update_stage(
        restApiId=api_id,
        stageName='prod',
        patchOperations=[
            {'op': 'replace', 'path': '/*/*/throttling/rateLimit', 'value': '2.0'},
            {'op': 'replace', 'path': '/*/*/throttling/burstLimit', 'value': '5'},
        ],
    )

    invoke_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
    print(f"  -> API Gateway Invoke URL: {invoke_url}")
    print(f"  -> Throttling configurado : Rate = 2.0 req/s | Burst = 5 solicitudes")
    return {
        'api_id': api_id,
        'invoke_url': invoke_url,
        'rate_limit': 2.0,
        'burst_limit': 5,
    }


def step_5_sns_and_cloudwatch_alarm(session, backend_instance_id: str) -> dict:
    sns = session.client('sns')
    cw = session.client('cloudwatch')
    print("\n[5/6] Configurando Tópico Amazon SNS y Alarma en Amazon CloudWatch...")

    topic_arn = sns.create_topic(Name='PetCare-CloudWatch-Alerts-SNS')['TopicArn']
    email_notify = os.environ.get('ALERT_EMAIL', '')
    if email_notify:
        sns.subscribe(TopicArn=topic_arn, Protocol='email', Endpoint=email_notify)

    alarm_name = 'PetCare-EC2-High-CPU-Alarm'
    cw.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription='Alarma EVA 4 PetCare: Uso de CPU en EC2 Backend >= 70% durante 5 minutos',
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        OKActions=[topic_arn],
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistic='Average',
        Dimensions=[{'Name': 'InstanceId', 'Value': backend_instance_id}],
        Period=300,
        EvaluationPeriods=1,
        Threshold=70.0,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='notBreaching',
    )
    print(f"  -> SNS Topic ARN   : {topic_arn}")
    print(f"  -> CloudWatch Alarm: {alarm_name} (CPUUtilization >= 70%)")
    return {'sns_topic_arn': topic_arn, 'alarm_name': alarm_name}


def step_6_lambda_and_eventbridge_7h(session, account_id: str, sns_topic_arn: str) -> dict:
    iam = session.client('iam')
    lam = session.client('lambda')
    events = session.client('events')
    print("\n[6/6] Configurando Función AWS Lambda + EventBridge Trigger cada 7 horas (rate(7 hours))...")

    # Resolver rol IAM (LabRole en AWS Academy o crear rol dedicado en cuenta estándar)
    role_arn = None
    for role_candidate in ('LabRole', 'vocstartsoft/LabRole', 'PetCareLambdaRDSBackupRole'):
        try:
            r = iam.get_role(RoleName=role_candidate.split('/')[-1])
            role_arn = r['Role']['Arn']
            break
        except ClientError:
            continue

    if not role_arn:
        assume_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Principal': {'Service': 'lambda.amazonaws.com'},
                    'Action': 'sts:AssumeRole',
                }
            ],
        }
        r = iam.create_role(
            RoleName='PetCareLambdaRDSBackupRole',
            AssumeRolePolicyDocument=json.dumps(assume_policy),
        )
        role_arn = r['Role']['Arn']
        for pol in (
            'arn:aws:iam::aws:policy/AmazonRDSFullAccess',
            'arn:aws:iam::aws:policy/AmazonSNSFullAccess',
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        ):
            iam.attach_role_policy(RoleName='PetCareLambdaRDSBackupRole', PolicyArn=pol)
        time.sleep(10)

    # Empaquetar aws_infra/lambda_rds_backup_7h.py en ZIP
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lambda_file = os.path.join(base_dir, 'lambda_rds_backup_7h.py')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(lambda_file, arcname='lambda_function.py')
    zip_bytes = buf.getvalue()

    fn_name = 'PetCare-RDS-Backup-Every-7-Hours'
    try:
        fn = lam.get_function(FunctionName=fn_name)
        fn_arn = fn['Configuration']['FunctionArn']
        lam.update_function_code(FunctionName=fn_name, ZipFile=zip_bytes)
    except ClientError:
        fn = lam.create_function(
            FunctionName=fn_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_bytes},
            Description='EVA 4 PetCare: Respaldo snapshot de RDS PostgreSQL cada 7 horas + alerta SNS',
            Timeout=60,
            MemorySize=128,
            Environment={
                'Variables': {
                    'RDS_INSTANCE_ID': RDS_INSTANCE_ID,
                    'SNS_TOPIC_ARN': sns_topic_arn,
                    'MAX_CUSTOM_SNAPSHOTS': '12',
                }
            },
        )
        fn_arn = fn['FunctionArn']

    # Crear regla en Amazon EventBridge cada 7 horas
    rule_name = 'PetCare-RDS-Backup-Every-7-Hours-Rule'
    rule_res = events.put_rule(
        Name=rule_name,
        ScheduleExpression='rate(7 hours)',
        State='ENABLED',
        Description='Dispara la funcion Lambda de respaldo de RDS PostgreSQL exactamente cada 7 horas',
    )
    rule_arn = rule_res['RuleArn']

    try:
        lam.add_permission(
            FunctionName=fn_name,
            StatementId='AllowEventBridgeInvokeEvery7Hours',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn,
        )
    except ClientError:
        pass

    events.put_targets(
        Rule=rule_name,
        Targets=[{'Id': '1', 'Arn': fn_arn}],
    )
    print(f"  -> Lambda ARN      : {fn_arn}")
    print(f"  -> EventBridge Rule: {rule_name} -> rate(7 hours)")
    return {'lambda_name': fn_name, 'lambda_arn': fn_arn, 'eventbridge_rule': rule_name}


def main():
    session = get_session()
    sts = session.client('sts')
    ident = sts.get_caller_identity()
    account_id = ident['Account']
    print("=" * 80)
    print(f"  INICIANDO APROVISIONAMIENTO AWS PETCARE EVA 4 (Cuenta AWS: {account_id})")
    print("=" * 80)

    s3_res = step_1_s3_bucket(session, account_id)
    ec2_res = step_2_discover_backend_and_launch_frontend_ec2(session)
    rds_res = step_3_rds_postgresql(session, ec2_res['vpc_id'], ec2_res['backend_sg_id'])
    apigw_res = step_4_api_gateway_with_rate_limit(session)
    cw_res = step_5_sns_and_cloudwatch_alarm(session, ec2_res['backend_instance_id'])
    lam_res = step_6_lambda_and_eventbridge_7h(session, account_id, cw_res['sns_topic_arn'])

    summary = {
        'aws_account_id': account_id,
        's3': s3_res,
        'ec2': ec2_res,
        'rds': rds_res,
        'api_gateway': apigw_res,
        'cloudwatch_sns': cw_res,
        'lambda_eventbridge_7h': lam_res,
    }
    with open('resumen_infraestructura_aws_eva4.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("  ✅ TODOS LOS SERVICIOS AWS DE LA EVALUACIÓN 4 HAN SIDO CREADOS")
    print("=" * 80)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
