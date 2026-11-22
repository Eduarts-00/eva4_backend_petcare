"""
Actividad 8 (Evaluación N.º 4): Función AWS Lambda para Respaldos Automatizados de
Amazon RDS PostgreSQL exactamente cada 7 horas (invocada por Amazon EventBridge Scheduler)
con notificación de alerta vía Amazon SNS.

Justificación Técnica:
Amazon RDS ofrece respaldos automáticos nativos únicamente con una ventana de respaldo diaria
(periodicidad de 24 horas) y retención de 1 a 35 días. Como RDS no posee un parámetro nativo
para ejecutar snapshots exactamente cada 7 horas, esta función Lambda se vincula a una regla
de Amazon EventBridge Scheduler con la expresión `rate(7 hours)`, generando un DB Snapshot
incremental cifrado con KMS y notificando el estado al administrador mediante Amazon SNS.
"""
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    region = os.environ.get('AWS_REGION', 'us-east-1')
    db_instance_id = os.environ.get('RDS_INSTANCE_ID', 'petcare-rds-postgres')
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
    retention_max_snapshots = int(os.environ.get('MAX_CUSTOM_SNAPSHOTS', '12'))

    rds = boto3.client('rds', region_name=region)
    sns = boto3.client('sns', region_name=region)

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M')
    snapshot_id = f"{db_instance_id}-7h-auto-{timestamp}"

    try:
        # 1. Crear el Snapshot de la instancia RDS PostgreSQL
        response = rds.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceIdentifier=db_instance_id,
            Tags=[
                {'Key': 'Project', 'Value': 'PetCare-EVA4'},
                {'Key': 'Schedule', 'Value': 'Every-7-Hours-EventBridge'},
                {'Key': 'ManagedBy', 'Value': 'AWS-Lambda'},
            ],
        )
        status_snap = response['DBSnapshot']['Status']

        # 2. Rotación preventiva de snapshots antiguos generados por esta Lambda
        eliminados = []
        snaps = rds.describe_db_snapshots(
            DBInstanceIdentifier=db_instance_id,
            SnapshotType='manual',
        ).get('DBSnapshots', [])
        propios = sorted(
            [s for s in snaps if '-7h-auto-' in s['DBSnapshotIdentifier'] and s['Status'] == 'available'],
            key=lambda x: x.get('SnapshotCreateTime', datetime.min.replace(tzinfo=timezone.utc)),
        )
        while len(propios) > retention_max_snapshots:
            viejo = propios.pop(0)
            rds.delete_db_snapshot(DBSnapshotIdentifier=viejo['DBSnapshotIdentifier'])
            eliminados.append(viejo['DBSnapshotIdentifier'])

        mensaje = (
            f"[PetCare EVA 4] Respaldo programado cada 7 horas ejecutado con éxito.\n"
            f"- Instancia RDS : {db_instance_id}\n"
            f"- Snapshot ID   : {snapshot_id}\n"
            f"- Estado inicial: {status_snap}\n"
            f"- Disparador    : Amazon EventBridge Scheduler — rate(7 hours)\n"
            f"- Snapshots antiguos rotados: {len(eliminados)}"
        )

        if sns_topic_arn:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject='[PetCare AWS RDS] Snapshot Automatizado (Cada 7 Horas) Iniciado',
                Message=mensaje,
            )

        return {
            'statusCode': 200,
            'snapshot_id': snapshot_id,
            'rds_instance': db_instance_id,
            'status': status_snap,
            'rotated_snapshots': eliminados,
        }

    except ClientError as exc:
        error_msg = f"[PetCare EVA 4 ERROR] Fallo al crear snapshot cada 7h en {db_instance_id}: {exc}"
        if sns_topic_arn:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject='[ALERTA PetCare RDS] Error en Respaldo Programado 7h',
                Message=error_msg,
            )
        raise
