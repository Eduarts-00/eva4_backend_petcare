# Registro de Uso y Apoyo de Herramientas de Inteligencia Artificial (`prompts_ia.md`)

**Proyecto:** Sistema de Gestión de Citas y Fichas Médicas para Veterinaria (**PetCare**)  
**Asignatura:** Desarrollo Backend — Evaluación Parcial N°3  
**Docente:** Marcelo Alvarado Aravena  
**Estudiante:** Angel Eduardo Lara Manriquez (Sección IEC-N4-C2)  
**Año:** 2026  

---

## 1. Propósito del Documento

En conformidad con la sección **IV (Apoyo de Inteligencia Artificial)** y el **Criterio 4 de la Rúbrica**, este documento detalla las consultas (prompts) realizadas al asistente de IA durante el ciclo de desarrollo, las orientaciones recibidas y las validaciones técnicas aplicadas sobre el código final.

---

## 2. Bitácora de Prompts y Apoyos Solicitados

### Prompt 1 — Modelado Relacional en PostgreSQL y Regla Anti-Solapamiento
> **Consulta realizada:**  
> *"Necesito estructurar en Django + PostgreSQL el modelo de datos para la veterinaria PetCare que cubra: Tutores, Mascotas, Profesionales con horario de atención, Citas Médicas sin solapamiento de horarios, Fichas Clínicas digitales (diagnóstico, tratamiento, receta y exámenes) y Recordatorios de Vacunación. ¿Cómo implemento la validación para impedir cruces de horario en un mismo veterinario?"*

- **Apoyo obtenido:** Diseño de entidades normalizadas en `clinica/models.py` con claves foráneas (`Tutor -> Mascota -> CitaMedica / FichaClinica / ControlVacuna`) y el algoritmo de intersección de intervalos `hora_inicio < existente.hora_fin` y `hora_fin > existente.hora_inicio` dentro del método `clean()` de `CitaMedica` protegido con `transaction.atomic()`.
- **Adaptación propia:** Se añadió cálculo automático de `hora_fin` según `duracion_bloque_min` del profesional (30 min por defecto) y actualización automática del peso de la mascota y estado `ATENDIDA` de la cita al emitir una `FichaClinica`.

---

### Prompt 2 — Personalización del Administrador de Django y Templates
> **Consulta realizada:**  
> *"¿Cómo personalizar el panel de Django Admin para registrar todos los modelos de PetCare con filtros laterales, búsqueda por RUT/mascota, edición en línea (Inlines), etiquetas visuales de colores (semáforo de vacunas vencidas/próximas) y un template personalizado `templates/admin/base_site.html`?"*

- **Apoyo obtenido:** Configuración en `clinica/admin.py` y `users/admin.py` utilizando `TabularInline`, `StackedInline`, `format_html` para insignias de estado y semáforos de vacunación, acciones masivas (`@admin.action`) y sobrecarga de `templates/admin/base_site.html` con paleta clínica institucional.

---

### Prompt 3 — Endpoints DRF, Disponibilidad Horaria y Seguridad por Roles
> **Consulta realizada:**  
> *"Necesito exponer los CRUD en Django REST Framework con autenticación híbrida (Sesiones de Django + JWT) para tres roles (ADMIN, VETERINARIO, TUTOR), además de un endpoint que devuelva los bloques libres y ocupados de un médico veterinario según la fecha seleccionada."*

- **Apoyo obtenido:** Implementación de `ProfesionalViewSet.disponibilidad` (`/api/profesionales/{id}/disponibilidad/?fecha=YYYY-MM-DD`), permisos personalizados `IsStaffClinicoOrReadOnly` e `IsVeterinarioOrAdmin` en `users/permissions.py`, e inicio de sesión unificado en `CustomLoginView` (creando cookie `sessionid` + token JWT).

---

### Prompt 4 — Interfaz Web Responsiva Integrada (Frontend SPA)
> **Consulta realizada:**  
> *"Genera una interfaz web responsiva en `templates/index.html` con Bootstrap 5 que consuma de forma asíncrona los endpoints REST de PetCare para administrar Tutores, Mascotas, Calendario de Citas con selector visual de bloques disponibles, Fichas Clínicas y Semáforo de Recordatorios de Vacunas."*

- **Apoyo obtenido:** Maquetación responsiva con panel de indicadores KPI en tiempo real, selector visual de bloques horarios (verdes disponibles / rojos ocupados), modales CRUD y control dinámico de botones según el rol autenticado.

---

### Prompt 5 — Sesión Unificada por Rango, Alta/Bloqueo de Médicos y Portada Informativa
> **Consulta realizada:**  
> *"Unifica el login para que Django Admin y la web usen la misma sesión según el rango del usuario, redirige cualquier ruta inexistente al inicio, diseña una portada pública informativa sobre los alcances de tratamiento para tutores, y permite que el Administrador cree cuentas temporales para nuevos médicos (exigiendo cambio de contraseña al primer ingreso) y pueda bloquear/inhabilitar cuentas ante despido o protección."*

- **Apoyo obtenido:** Implementación de `RedirectUnknownRoutesMiddleware`, redirección unificada de `/admin/login/` y `/admin/logout/`, campo `debe_cambiar_password` en `CustomUser` con modal de cambio seguro obligatorio (`CambiarPasswordView`), y acciones administrativas `cambiar_estado_cuenta` (con cierre inmediato de sesiones activas) y `asignar_credenciales`.

---

### Prompt 6 — Script de Despliegue Productivo en AWS EC2 (`98.85.49.169`)
> **Consulta realizada:**  
> *"Necesito configurar y desplegar el proyecto PetCare junto con su base de datos PostgreSQL en la instancia Ubuntu de AWS Academy EC2 (IP Elástica `98.85.49.169`) usando Gunicorn (socket Unix systemd) y Nginx como proxy inverso sirviendo archivos estáticos."*

- **Apoyo obtenido:** Configuración de servicio `/etc/systemd/system/gunicorn.service`, configuración de proxy inverso `/etc/nginx/sites-available/petcare`, recolección de estáticos (`collectstatic`) y ajuste de permisos de grupo `ubuntu:www-data`.

---

## 3. Verificación y Pruebas Realizadas

1. **Integridad Relacional PostgreSQL:** Verificación de migraciones limpias (`makemigrations` y `migrate`) sobre motor `django.db.backends.postgresql`.
2. **Bloqueo de Solapamiento:** Intento de agendar dos citas a la misma hora con el mismo veterinario retorna HTTP `400 Bad Request` detallando el conflicto horario.
3. **Seguridad y Sesiones:** Validación de acceso restringido a endpoints clínicos para usuarios no autenticados (`401/403`) y segregación de vistas para el rol `TUTOR`.
4. **Django Admin y OpenAPI:** Comprobación visual de `/admin/` personalizado y `/api/docs/` (Swagger UI).
