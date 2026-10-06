## CHATTER IA: Modulo para Odoo

<h5 style="border-bottom: 2px solid #ccc; padding-bottom: 10px;">Instalación</h5>

* Instalacion con docker-compose.yml integrado


<p>Puedes usar el docker-compose.yml. Crear un archivo .env y copia la información del archivo ".env.example" y ajusta los parametros necesarios.</p>

```ini
    # .env
    PROJECT_NAME=chatteria
    POSTGRES_VERSION=14
    ODOO_VERSION=19.0
    POSTGRES_USER=odoo
    POSTGRES_PASSWORD=odoo 
    POSTGRES_DB=postgres
    HOST=db
    USER=odoo 
    PASSWORD=1234 
```

* Instalacion en instancia activa:

<p>Si ya posees una instancia activa solo mueve el addon "chatteria" a tus addons custom.</p>

<br/>

<h5 style="border-bottom: 2px solid #ccc; padding-bottom: 10px;">Implementar el boton flotante</h5>

* Configuracion de nuevo token de API en Odoo:

<p> El modulo "chatteria" agrega dos nuevos campos en la compañia llamados; Gemini Token Access y Allowed Urls. Estos campos se encargan de almacenar el token de gemini y los dominios desde donde se pueden conectar como mecanismos de seguridad.

Para obtener el token ve a <a href="https://aistudio.google.com/api-keys">https://aistudio.google.com/api-keys</a>.
</p>


* Registrar el token de gemini:
<p> Una vez obtenido el token de gemini, dentro de odoo ve a: <b>Ajustes > Usuarios y Empresas > Empresas > (Selecciona empresa)</b>

La ficha de empresa tiene un nuevo page llamado "<b>Security Gemini</b>" y alli encontraras el campo "<b>Gemini Token Access</b>" pega tu token y guarda.

Adicionalmente puedes definir las rutas a las que se tendra acceso con ese token (url del cliente) en el campo <b>Allowed URls</b>
</p>

* Crea la API de usuario:

<p> Crea un usuario para la instancia del cliente, por ejemplo "cliente1@empresa.com", asignale el permiso "<b>Gemini Group</b>" y la clave. 

1. Inicia sesion con el usuario y ve al icono de usuario en la parte superior derecha de la pantalla.
2. Mis preferencias.
3. En el modal ve a "Seguridad".
4. Agregar Clave API, coloca tu clave, confirma.
5. Indica el nombre de la app para la api por ejemplo "Chatter IA" y Genera la clave
6. Copia y guarda esa clave que sera unica para el cliente.
</p>


* Incrustar el Chatter en tu sitio web con clave API de usuario:

El cliente necesitara que el script proporcionado cuente con la url del odoo y un token de usuario generado previamente, ejemplo:

```html
<!-- 
 
odoo_url: Url del dominio odoo por ejemplo: https://www.miweb.com

token: Es el token de usuario (Api generada previamente) por ejmplo: f157959b2ce15ae3bff69a4100e27c589c05e77f

remind: Puede ser 1 o 0 y representa si el chatter conversara el historial tras actualizar o no -->
<script 
    defer 
    src="{odoo_url}/chatteria/source.js?token={odoo_token}&remind=1">
</script>
```

<p>Una vez que el cliente incruste este codigo en su web automaticamente se habilitara el boton flotante </p>