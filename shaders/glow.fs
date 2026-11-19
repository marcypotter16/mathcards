#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 glowColor;    // Colore del bagliore esterno
uniform float glowWidth;   // Spessore del bagliore (es. 4.0 - 8.0)
uniform vec2 textureSize;  // Dimensione della texture in pixel

// Angoli di rotazione per una leggera risposta alla luce
uniform float x_rot;
uniform float y_rot;

out vec4 finalColor;

void main() {
    vec4 texel = texture(texture0, fragTexCoord);
    
    // 1. GESTIONE DEL GLOW ESTERNO (Morbido e sfumato)
    if (texel.a < 0.1) {
        float glow = 0.0;
        vec2 texelSize = 1.0 / textureSize;
        
        for (float x = -glowWidth; x <= glowWidth; x++) {
            for (float y = -glowWidth; y <= glowWidth; y++) {
                float dist = length(vec2(x, y));
                if (dist <= glowWidth) {
                    vec4 sample = texture(texture0, fragTexCoord + vec2(x, y) * texelSize);
                    // Sfumatura lineare e morbida verso l'esterno
                    float falloff = smoothstep(glowWidth, 0.0, dist);
                    glow = max(glow, sample.a * falloff);
                }
            }
        }
        
        if (glow > 0.01) {
            finalColor = vec4(glowColor.rgb, glow * glowColor.a);
        } else {
            finalColor = vec4(0.0);
        }
        return;
    }

    // 2. SUPERFICIE DELLA CARTA (Pulita con riflesso appena accennato)
    vec4 baseColor = texel * fragColor;
    vec2 uv = fragTexCoord;
    
    // Calcola una leggera inclinazione della luce
    vec2 tilt = vec2(y_rot, -x_rot) * 0.025;
    vec2 lightCenter = vec2(0.5) + tilt;
    
    // Crea un gradiente morbido e ampio (non una striscia netta)
    float distFromLight = length(uv - lightCenter);
    float softSheen = smoothstep(0.8, 0.0, distFromLight);
    
    // Applica solo un 12% di luce extra (0.12) per non distrarre
    // vec3 finalRGB = baseColor.rgb + vec3(1.0) * softSheen * 0.12;
    
    // Leggerissimo bordo interno luminoso (rim light) dello stesso colore del glow
    float edgeDist = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
    float innerRim = smoothstep(0.06, 0.0, edgeDist);
    // finalRGB += glowColor.rgb * innerRim * 0.15;
    // Aggiungi questa riga nel Fragment Shader per legare la luce interna all'inclinazione
    float tiltAmount = clamp((abs(x_rot) + abs(y_rot)) / 15.0, 0.0, 1.0);
    vec3 finalRGB = baseColor.rgb + vec3(1.0) * softSheen * (0.12 * tiltAmount);
    finalRGB += glowColor.rgb * innerRim * (0.15 * tiltAmount);


    finalColor = vec4(finalRGB, baseColor.a);
    // finalColor = vec4(1.0, 1.0, 1.0, 1.0)
}
