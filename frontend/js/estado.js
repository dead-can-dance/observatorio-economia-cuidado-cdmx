// Estado compartido entre secciones.
//   ficha: alcaldía cuya ficha se muestra en la sección de alcaldías.
//   mapa:  alcaldía que enfoca el mapa del territorio (null = toda la ciudad).
// Son independientes a propósito: elegir una ficha no mueve el mapa. El botón
// «Ver en el mapa» de la ficha es el que los conecta.

import { reactive } from 'vue';

export const seleccion = reactive({ ficha: null, mapa: null });

// Etiquetas cortas para los ejes. La tabla de cada gráfica conserva el nombre completo.
const CORTAS = {
  'Cuidado a integrantes del hogar (total)': 'Cuidado a integrantes del hogar (total)',
  'Cuidado a niñas/os de 0 a 5': 'Niñas y niños de 0 a 5',
  'Cuidado a niñas y niños de 0 a 5': 'Niñas y niños de 0 a 5',
  'Cuidado a niñas y niños de 6 a 14': 'Niñas y niños de 6 a 14',
  'Cuidado a personas de 60+': 'Personas de 60 años o más',
  'Cuidados especiales (enfermedad o discapacidad)': 'Cuidados especiales (enfermedad o discapacidad)',
  'Trabajo doméstico no remunerado': 'Trabajo doméstico no remunerado',
};

export const corta = (actividad) => CORTAS[actividad] ?? actividad;
