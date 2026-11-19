#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord; // Corretto: 'on' -> 'in', rimosso spazio in 'vertexTexCoord'
in vec4 vertexColor;    // Corretto: 'on' -> 'in'

uniform mat4 mvp;
uniform vec2 cardCenter;
uniform vec2 cardSize;
uniform float fov;
uniform float y_rot;
uniform float x_rot;
uniform float inset;

out vec2 fragTexCoord;
out vec4 fragColor;

void main() {
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;

    // 1. Centra la carta e applica l'inset
    vec2 local = (vertexPosition.xy - cardCenter) * (1.0 - inset);

    // 2. Rotazioni 3D
    float yaw = radians(y_rot);
    float pitch = radians(x_rot);
    // abbassiamo gli angoli un po'
    yaw = yaw * 0.4;
    pitch = pitch * 0.4;
    vec3 p = vec3(local, 0.0);

    p = vec3(
        cos(yaw) * p.x + sin(yaw) * p.z,
        p.y,
        -sin(yaw) * p.x + cos(yaw) * p.z
    );

    p = vec3(
        p.x,
        cos(pitch) * p.y - sin(pitch) * p.z,
        sin(pitch) * p.y + cos(pitch) * p.z
    );

    // 3. Calcola la distanza della camera
    float camera_distance = (cardSize.y * 0.5) / tan(radians(fov) * 0.5);

    // 4. Calcola il divisore prospettico (w)
    float w = max(camera_distance - p.z, camera_distance * 0.1) / camera_distance;

    // 5. Calcola la posizione sullo schermo SENZA dividere per w
    vec2 screenPos = cardCenter + p.xy;

    // 6. Trasforma con la matrice mvp (ortografica)
    vec4 clipPos = mvp * vec4(screenPos, vertexPosition.z, 1.0);

    // 7. Applica w alle coordinate clip: la GPU farà la divisione prospettica corretta!
    gl_Position = vec4(clipPos.xy, clipPos.z * w, w);
    // gl_Position = vec4(1.0, 1.0, 1.0, 1.0)
}
