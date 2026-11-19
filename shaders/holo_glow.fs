#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 glowColor;    // Colore del bordo (es. arancione/viola)
uniform float glowWidth;   // Spessore del bordo (es. 4.0 - 8.0)
uniform vec2 textureSize;  // Dimensione texture in pixel

// Passa gli stessi angoli del vertex shader per animare i riflessi!
uniform float x_rot;
uniform float y_rot;

out vec4 finalColor;

// Funzione per generare colori arcobaleno fluidi (Cosine Palette)
vec3 holoPalette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}

void main() {
    vec4 texel = texture(texture0, fragTexCoord);
    
    // 1. GESTIONE DEL GLOW ESTERNO (Sfumato e morbido)
    if (texel.a < 0.1) {
        float glow = 0.0;
        vec2 texelSize = 1.0 / textureSize;
        
        for(float x = -glowWidth; x <= glowWidth; x++) {
            for(float y = -glowWidth; y <= glowWidth; y++) {
                float dist = length(vec2(x, y));
                if (dist <= glowWidth) {
                    vec4 sample = texture(texture0, fragTexCoord + vec2(x, y) * texelSize);
                    // Sfumatura morbida in base alla distanza dal bordo
                    float falloff = 1.0 - (dist / glowWidth);
                    glow = max(glow, sample.a * falloff);
                }
            }
        }
        
        if (glow > 0.01) {
            // Fa pulsare leggermente il glow quando inclini la carta
            float tiltBoost = 1.0 + (abs(x_rot) + abs(y_rot)) * 0.01;
            finalColor = vec4(glowColor.rgb * tiltBoost, glow * glowColor.a);
        } else {
            finalColor = vec4(0.0);
        }
        return;
    }

    // 2. EFFETTO CARTA OLOGRAFICA & SPECULARE
    vec4 baseColor = texel * fragColor;
    vec2 uv = fragTexCoord;
    
    // Calcola il vettore di inclinazione normalizzato
    vec2 tilt = vec2(y_rot, -x_rot) * 0.03;

    // A. Trama Olografica Arcobaleno (si muove con l'inclinazione)
    float holoAngle = (uv.x * 1.5 + uv.y * 1.5) + (tilt.x + tilt.y) * 1.8;
    vec3 rainbow = holoPalette(holoAngle);

    // B. Micro-pattern "Foil" diagonale (righe sottili tipiche delle carte rare)
    float foilPattern = sin((uv.x - uv.y) * 180.0 + tilt.x * 10.0) * 0.5 + 0.5;
    foilPattern = pow(foilPattern, 3.0); // Rende le linee più nitide

    // C. Fascio di luce speculare (Glare) che attraversa la carta
    vec2 lightPos = vec2(0.5) + tilt * 1.2;
    // Crea una striscia diagonale luminosa
    float glareLine = 1.0 - abs((uv.x - lightPos.x) + (uv.y - lightPos.y));
    float specular = pow(clamp(glareLine, 0.0, 1.0), 6.0);

    // D. Maschera di intensità: fa brillare di più le zone chiare/disegnate
    // e meno lo sfondo scuro della carta
    float luminance = dot(baseColor.rgb, vec3(0.299, 0.587, 0.114));
    float holoMask = mix(0.25, 0.85, luminance); // 0.25 sullo sfondo scuro, 0.85 sui disegni chiari

    // Combina l'effetto olografico con il colore originale
    vec3 holoEffect = rainbow * (0.6 + 0.4 * foilPattern) * holoMask;
    vec3 finalRGB = baseColor.rgb + holoEffect * 0.55; // 0.55 controlla la forza dell'arcobaleno
    
    // Aggiunge il riflesso bianco speculare sopra tutto
    finalRGB += vec3(1.0, 0.98, 0.95) * specular * 0.45;

    finalColor = vec4(finalRGB, baseColor.a);
}

