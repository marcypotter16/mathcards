#version 330
in vec2 fragTexCoord;
in vec4 fragColor;
uniform sampler2D texture0;
uniform vec4 glowColor;  // Pass your orange/purple color here
uniform float glowWidth; // How thick the glow is (e.g., 2.0 to 8.0)
uniform vec2 textureSize; // Size of the card texture

out vec4 finalColor;

void main() {
    vec4 texel = texture(texture0, fragTexCoord);
    
    // If the current pixel is fully transparent, calculate glow
    if (texel.a < 0.1) {
        float glow = 0.0;
        vec2 texelSize = 1.0 / textureSize;
        
        // Sample neighboring pixels in a circle
        for(float x = -glowWidth; x <= glowWidth; x++) {
            for(float y = -glowWidth; y <= glowWidth; y++) {
                vec4 sample = texture(texture0, fragTexCoord + vec2(x, y) * texelSize);
                glow = max(glow, sample.a);
            }
        }
        
        // Only draw the glow if a neighbor is opaque
        if (glow > 0.0) {
            finalColor = vec4(glowColor.rgb, glow * glowColor.a);
        } else {
            finalColor = vec4(0.0); // Transparent
        }
    } else {
        // Draw the card itself normally
        finalColor = texel * fragColor;
    }
}