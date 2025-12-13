// ==========================================
// === PARÁMETROS DE ANIMACIÓN Y ESCENA ===
// ==========================================

// --- Parámetros de Configuración del Tanque ---
$fn = 100;               // Resolución (suavizado)
largo_tanque = 800;      // Largo de la parte recta
diametro_tanque = 320;   // Grosor del tanque
ancho_cinta = 40;        // Ancho de las fajas negras
separacion_cintas = 200; // Distancia de las cintas desde el centro

// --- Parámetros del Anillo Power-up ---
gap_anillo = 15;         // ESPACIO entre el tanque y el anillo (Estilo Saturno)
alto_anillo_purple = 100; // Altura total de la cápsula púrpura
grosor_anillo = 25;      // Qué tan "gordo" es el anillo hacia afuera
tamano_texto = 22;       // Tamaño de las letras GNC

// --- PALETA DE COLORES (Vectores RGB [R, G, B]) ---
color_tanque = [1.0, 0.827, 0.259];   // Amarillo específico
color_cintas = [0.15, 0.15, 0.15];   // Gris carbón casi negro
color_powerup_glow = [0.7, 0.0, 1.0]; // Violeta eléctrico vibrante
color_banda = [1.0, 1.0, 1.0];       // Blanco puro
color_texto = [0.05, 0.05, 0.05];    // Negro casi puro

// --- VARIABLES DE ANIMACIÓN ---
// $t es una variable de OpenSCAD que va de 0 a 1 durante la animación.
angulo_orbital = $t * 360;       // Rotación completa alrededor del centro global
angulo_giro_propio = $t * 360 * 3; // Gira sobre sí mismo 3 veces más rápido
inclinacion_pisa = 20;           // Grados de inclinación "Torre de Pisa"


// ==========================================
// === RENDERIZADO Y ANIMACIÓN ===
// ==========================================

// Las transformaciones se leen de abajo hacia arriba (del objeto hacia afuera)

rotate([0, angulo_orbital, 0])           // 5. Rotación Orbital: Gira todo el conjunto alrededor del eje Y global
translate([0, largo_tanque/2 * sin(inclinacion_pisa), 0]) // 4b. Ajuste fino de altura para que no se hunda en el piso al inclinarse
rotate([0, 0, -inclinacion_pisa])        // 4. Inclinación Pisa: Inclina el objeto sobre el eje Z
rotate([0, angulo_giro_propio, 0])       // 3. Giro Propio: Gira sobre su NUEVO eje Y (que ahora es vertical)
rotate([0, 0, 90])                       // 2. Reorientación Inicial: Paramos el tanque para que el eje Y sea su largo
rotate([90,0,0])                         // 1. Ajuste de cámara para verlo mejor
escena_completa();


// ==========================================
// === MÓDULOS DEL OBJETO ===
// ==========================================

// --- Módulo Principal (Agrupa todo) ---
module escena_completa() {
    tubo_gnc_base();
    anillo_powerup();
}

// --- Módulo del Tubo Base ---
module tubo_gnc_base() {
    color(color_tanque) {
        hull() {
            translate([-largo_tanque/2, 0, 0]) sphere(d=diametro_tanque);
            translate([largo_tanque/2, 0, 0]) sphere(d=diametro_tanque);
        }
    }
    color(color_cintas) {
        translate([-separacion_cintas, 0, 0]) rotate([0, 90, 0])
            difference() {
                cylinder(d=diametro_tanque + 10, h=ancho_cinta, center=true);
                cylinder(d=diametro_tanque - 1, h=ancho_cinta+2, center=true);
            }
        translate([separacion_cintas, 0, 0]) rotate([0, 90, 0])
            difference() {
                cylinder(d=diametro_tanque + 10, h=ancho_cinta, center=true);
                cylinder(d=diametro_tanque - 1, h=ancho_cinta+2, center=true);
            }
    }
}

// --- Módulo: Anillo Estilo Power-up ---
module anillo_powerup() {
    radio_interno = (diametro_tanque / 2) + gap_anillo;
    radio_externo = radio_interno + grosor_anillo;
    radio_centro_perfil = (radio_interno + radio_externo) / 2;
    radio_perfil_capsula = (radio_externo - radio_interno) / 2;

    rotate([0, 90, 0]) {
        // 1. La base Púrpura Brillante (Translúcida)
        color(color_powerup_glow, alpha=0.6) {
            rotate_extrude() {
                translate([radio_centro_perfil, 0, 0])
                hull() {
                    translate([0, (alto_anillo_purple/2) - radio_perfil_capsula]) circle(r=radio_perfil_capsula);
                    translate([0, -(alto_anillo_purple/2) + radio_perfil_capsula]) circle(r=radio_perfil_capsula);
                }
            }
        }
        // 2. La Banda Blanca Central
        color(color_banda) {
            rotate_extrude() {
                translate([radio_externo - 2, -alto_anillo_purple/4, 0]) square([4, alto_anillo_purple/2]);
            }
        }
        // 3. Texto GNC Frontal
        color(color_texto) {
            translate([0, -radio_externo - 1, 0]) 
            rotate([90, 0, 0]) 
            linear_extrude(height = 5) {
                text("GNC", font = "Arial Black", size = tamano_texto, valign = "center", halign = "center", spacing=1.1);
            }
        }
        // 4. Texto GNC Trasero
         color(color_texto) {
            translate([0, radio_externo + 1, 0]) 
            rotate([90, 0, 180]) 
            linear_extrude(height = 5) {
                 text("GNC", font = "Arial Black", size = tamano_texto, valign = "center", halign = "center", spacing=1.1);
            }
        }
    }
}