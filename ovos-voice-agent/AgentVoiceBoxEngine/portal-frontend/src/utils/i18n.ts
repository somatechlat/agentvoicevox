/**
 * Lightweight i18n implementation for Lit 3 without heavy dependencies.
 */

// Supported languages
export type SupportedLanguage = 'en' | 'es';

// Global state
let currentLanguage: SupportedLanguage = 'en';
const listeners: Set<() => void> = new Set();

// Dictionary structure
const translations: Record<SupportedLanguage, Record<string, string>> = {
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.settings': 'Settings',
    'nav.cloning': 'Voice Cloning',
    'settings.title': 'OVOS Configuration',
    'settings.subtitle': 'Manage the OpenVoiceOS cognitive core parameters.',
    'settings.advanced_mode': 'Advanced Mode (Raw JSON)',
    'settings.switch_ui': 'Switch to UI Forms',
    'settings.edit_json': 'Edit Raw JSON',
    'settings.btn_apply': 'Apply Configuration to Node',
    'settings.btn_applying': 'Applying...',
    'settings.core': 'Core Intelligence',
    'settings.lang': 'Primary Language',
    'settings.tts': 'Text-to-Speech (TTS) Engine',
    'settings.stt': 'Speech-to-Text (STT) Engine',
    'settings.vad': 'Listener & Audio (VAD)',
    'settings.vad_energy': 'Energy Ratio Threshold',
    'settings.log_level': 'System Log Level',
    'settings.skills': 'Skills Management',
    'settings.skills.blacklisted': 'Blacklisted Skills (comma separated)',
    'settings.skills.auto_update': 'Auto Update Skills',
    'settings.skills.priority': 'Priority Skills',
    'settings.location': 'Location Settings',
    'settings.location.city': 'City',
    'settings.location.timezone': 'Timezone',
    'settings.gui': 'GUI / Enclosure',
    'settings.gui.idle': 'Idle Screen Display',
    'tooltip.lang': 'The default language code for the system (e.g., en-us, es-es).',
    'tooltip.tts': 'The engine used to synthesize text into spoken audio.',
    'tooltip.stt': 'The engine used to transcribe spoken audio into text.',
    'tooltip.vad_energy': 'Controls Voice Activity Detection sensitivity. Higher values make it less sensitive to noise.',
    'tooltip.log_level': 'The verbosity of system logs. DEBUG provides the most information.',
    'tooltip.skills.blacklisted': 'A list of skill IDs that should not be loaded.',
    'tooltip.skills.auto_update': 'Automatically check for and apply updates to installed skills.',
    'tooltip.skills.priority': 'Skills that should be given higher priority during intent matching.',
    'tooltip.location.city': 'The physical city the device is located in, used by weather and time skills.',
    'tooltip.location.timezone': 'The timezone for scheduling and time-based skills.',
    'tooltip.gui.idle': 'What to display on the screen when no skill is active.',
    'cloning.title': 'Voice Cloning Library',
    'cloning.subtitle': 'Upload high-quality audio samples to clone voices for your agents.',
    'cloning.clone_new': 'Clone a New Voice',
    'cloning.voice_name': 'Voice Name',
    'cloning.language': 'Language',
    'cloning.audio_sample': 'Audio Sample (WAV/MP3)',
    'cloning.btn_start': 'Start Cloning Process',
    'cloning.btn_uploading': 'Uploading...',
  },
  es: {
    'nav.dashboard': 'Panel Principal',
    'nav.settings': 'Configuración',
    'nav.cloning': 'Clonación de Voz',
    'settings.title': 'Configuración OVOS',
    'settings.subtitle': 'Gestiona los parámetros del núcleo cognitivo OpenVoiceOS.',
    'settings.advanced_mode': 'Modo Avanzado (JSON Crudo)',
    'settings.switch_ui': 'Cambiar a Interfaz Visual',
    'settings.edit_json': 'Editar JSON Crudo',
    'settings.btn_apply': 'Aplicar Configuración al Nodo',
    'settings.btn_applying': 'Aplicando...',
    'settings.core': 'Inteligencia Central',
    'settings.lang': 'Idioma Principal',
    'settings.tts': 'Motor de Texto a Voz (TTS)',
    'settings.stt': 'Motor de Voz a Texto (STT)',
    'settings.vad': 'Escucha y Audio (VAD)',
    'settings.vad_energy': 'Umbral de Relación de Energía',
    'settings.log_level': 'Nivel de Registro (Log)',
    'settings.skills': 'Gestión de Habilidades (Skills)',
    'settings.skills.blacklisted': 'Habilidades Bloqueadas (separadas por coma)',
    'settings.skills.auto_update': 'Actualizar Habilidades Automáticamente',
    'settings.skills.priority': 'Habilidades Prioritarias',
    'settings.location': 'Configuración de Ubicación',
    'settings.location.city': 'Ciudad',
    'settings.location.timezone': 'Zona Horaria',
    'settings.gui': 'Interfaz Gráfica / Entorno',
    'settings.gui.idle': 'Pantalla en Reposo',
    'tooltip.lang': 'El código de idioma predeterminado (ej., en-us, es-es).',
    'tooltip.tts': 'El motor utilizado para sintetizar texto en audio.',
    'tooltip.stt': 'El motor utilizado para transcribir audio a texto.',
    'tooltip.vad_energy': 'Controla la sensibilidad de detección de voz. Valores más altos reducen la sensibilidad al ruido.',
    'tooltip.log_level': 'Nivel de detalle de los registros del sistema. DEBUG provee la máxima información.',
    'tooltip.skills.blacklisted': 'Lista de IDs de habilidades que no deben cargarse.',
    'tooltip.skills.auto_update': 'Buscar y aplicar actualizaciones automáticamente a las habilidades instaladas.',
    'tooltip.skills.priority': 'Habilidades que tendrán mayor prioridad al buscar coincidencias de intención.',
    'tooltip.location.city': 'La ciudad física donde se encuentra el dispositivo.',
    'tooltip.location.timezone': 'La zona horaria para tareas programadas.',
    'tooltip.gui.idle': 'Qué mostrar en la pantalla cuando ninguna habilidad está activa.',
    'cloning.title': 'Biblioteca de Clonación',
    'cloning.subtitle': 'Sube muestras de audio de alta calidad para clonar voces.',
    'cloning.clone_new': 'Clonar una Nueva Voz',
    'cloning.voice_name': 'Nombre de la Voz',
    'cloning.language': 'Idioma',
    'cloning.audio_sample': 'Muestra de Audio (WAV/MP3)',
    'cloning.btn_start': 'Iniciar Clonación',
    'cloning.btn_uploading': 'Subiendo...',
  }
};

/**
 * Translate a key into the current language.
 * @param key The translation key
 * @returns The translated string, or the key itself if not found
 */
export function t(key: string): string {
  const dict = translations[currentLanguage];
  return dict[key] || key;
}

/**
 * Change the current language and notify all listeners.
 * @param lang 'en' or 'es'
 */
export function setLanguage(lang: SupportedLanguage) {
  if (currentLanguage !== lang && translations[lang]) {
    currentLanguage = lang;
    notifyListeners();
  }
}

export function getCurrentLanguage(): SupportedLanguage {
  return currentLanguage;
}

/**
 * Register a callback to be called when the language changes.
 * Useful for forcing a re-render in Lit components.
 */
export function onLanguageChange(callback: () => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function notifyListeners() {
  listeners.forEach(cb => cb());
}
