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

// --- PALETA DE COLORES MEJORADA (Vectores RGB [R, G, B]) ---
// Amarillo industrial rico en lugar de "Gold" plano
//color_tanque = [0.95, 0.75, 0.1]; 
color_tanque = [1.0, 0.827, 0.259];  
// Gris carbón muy oscuro casi negro para las correas (parece goma/metal mate)
color_cintas = [0.15, 0.15, 0.15]; 
// Violeta eléctrico vibrante para el power-up
color_powerup_glow = [0.7, 0.0, 1.0]; 
// Blanco puro para la banda
color_banda = [1.0, 1.0, 1.0];
// Negro casi puro para el texto para máximo contraste
color_texto = [0.05, 0.05, 0.05];


// --- Módulo Principal ---
module escena_completa() {
    // Dibujamos el tanque original
    tubo_gnc_base();
    
    // Dibujamos el nuevo anillo estilo power-up justo en el centro
    anillo_powerup();
}

// --- Módulo del Tubo Base (Tu diseño original) ---
module tubo_gnc_base() {
    color(color_tanque) { // Usamos el nuevo color amarillo industrial
        hull() {
            translate([-largo_tanque/2, 0, 0]) sphere(d=diametro_tanque);
            translate([largo_tanque/2, 0, 0]) sphere(d=diametro_tanque);
        }
    }
    color(color_cintas) { // Usamos el nuevo gris carbón oscuro
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
    // Válvula (comentada como en tu código original)
    /*
    color("Silver") {
        translate([(largo_tanque/2) + (diametro_tanque/2) - 15, 0, 0])
            rotate([0, 90, 0]) cylinder(d=50, h=40);
        translate([(largo_tanque/2) + (diametro_tanque/2) + 20, 0, 0])
            rotate([0, 90, 0]) cylinder(d=30, h=20);
    }
    */ 
}

// --- NUEVO MÓDULO: Anillo Estilo Power-up ---
module anillo_powerup() {
    
    // Cálculos de radios para el espacio (gap)
    radio_interno = (diametro_tanque / 2) + gap_anillo;
    radio_externo = radio_interno + grosor_anillo;
    radio_centro_perfil = (radio_interno + radio_externo) / 2;
    radio_perfil_capsula = (radio_externo - radio_interno) / 2;

    // Rotamos todo 90 grados para que el anillo rodee el tanque horizontal
    rotate([0, 90, 0]) {
        
        // 1. La base Púrpura Brillante (Translúcida)
        // Usamos el nuevo color violeta eléctrico con transparencia
        color(color_powerup_glow, alpha=0.6) {
            rotate_extrude() {
                translate([radio_centro_perfil, 0, 0])
                hull() {
                    translate([0, (alto_anillo_purple/2) - radio_perfil_capsula])
                        circle(r=radio_perfil_capsula);
                    translate([0, -(alto_anillo_purple/2) + radio_perfil_capsula])
                        circle(r=radio_perfil_capsula);
                }
            }
        }

        // 2. La Banda Blanca Central
        color(color_banda) {
            rotate_extrude() {
                translate([radio_externo - 2, -alto_anillo_purple/4, 0])
                    square([4, alto_anillo_purple/2]);
            }
        }
        
        // 3. El Texto GNC (Estilo Pixel/Bloque)
        color(color_texto) {
            translate([0, -radio_externo - 1, 0]) // Posición en el borde exterior
            rotate([90, 0, 0]) // Girar para que mire al frente
            linear_extrude(height = 5) {
                // Nota: He simplificado la fuente a "Arial Black" para mayor compatibilidad. 
                // Si tienes una fuente específica de pixel art instalada, úsala aquí.
                text("GNC", font = "Arial Black", size = tamano_texto, valign = "center", halign = "center", spacing=1.1);
            }
        }
        
        // Texto GNC trasero
         color(color_texto) {
            translate([0, radio_externo + 1, 0]) 
            rotate([90, 0, 180]) 
            linear_extrude(height = 5) {
                 text("GNC", font = "Arial Black", size = tamano_texto, valign = "center", halign = "center", spacing=1.1);
            }
        }
    }
}

// --- Renderizado Final ---
escena_completa();