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
    'settings.title': 'OVOS & Agent Administration',
    'settings.subtitle': 'Full-stack configuration for your sovereign cognitive engines.',
    'settings.advanced_mode': 'Advanced JSON Editor',
    'settings.switch_ui': 'Switch to GUI',
    'settings.edit_json': 'Edit Raw Config',
    'settings.btn_apply': 'Apply to Cluster',
    'settings.btn_applying': 'Applying...',
    
    // Sidebar Tabs
    'tab.core': 'General & Location',
    'tab.audio': 'Audio & Speech (STT/TTS)',
    'tab.plugins': 'Plugins (Wake Word/VAD)',
    'tab.pipeline': 'Intent Pipelines',
    'tab.transformers': 'Transformers',
    'tab.skills': 'Skills & Dialog',

    // Core Tab
    'settings.lang': 'System Language',
    'settings.log_level': 'Log Level',
    'settings.location.city': 'City',
    'settings.location.timezone': 'Timezone',
    'settings.gui.idle': 'Idle Display Screen',

    // Audio Tab
    'settings.tts': 'Text-to-Speech Engine',
    'settings.stt': 'Speech-to-Text Engine',

    // Plugins Tab
    'settings.wakeword.module': 'Wake Word Engine',
    'settings.wakeword.threshold': 'Wake Word Threshold',
    'settings.vad.module': 'VAD Module',
    'settings.vad_energy': 'VAD Energy Ratio',

    // Pipeline Tab
    'settings.pipeline.order': 'Intent Pipeline Execution Order',

    // Transformers Tab
    'settings.transformers.audio': 'Audio Transformers',
    'settings.transformers.utterance': 'Utterance Transformers',
    'settings.transformers.dialog': 'Dialog Transformers',

    // Skills Tab
    'settings.skills.auto_update': 'Auto Update Skills',
    'settings.skills.blacklisted': 'Blacklisted Skills',
    'settings.skills.priority': 'Priority Skills',
    'settings.continuous.enabled': 'Continuous Conversation',
    'settings.continuous.prompts': 'Follow-up Prompts',

    // Tooltips
    'tooltip.lang': 'The default language code for the system (e.g., en-us, es-es).',
    'tooltip.log_level': 'Verbosity of logs (DEBUG, INFO, WARNING, ERROR).',
    'tooltip.location.city': 'The physical city, used by weather and time skills.',
    'tooltip.location.timezone': 'The timezone for scheduling.',
    'tooltip.gui.idle': 'Skill to display when idle.',
    'tooltip.tts': 'The module responsible for generating voice.',
    'tooltip.stt': 'The module responsible for transcribing user audio.',
    'tooltip.wakeword.module': 'Engine that listens for the hotword (e.g., precise, pocket-sphinx).',
    'tooltip.wakeword.threshold': 'Sensitivity of the wake word engine.',
    'tooltip.vad.module': 'Voice Activity Detection engine (e.g., silero).',
    'tooltip.vad_energy': 'Higher values make VAD less sensitive to background noise.',
    'tooltip.pipeline.order': 'Comma-separated order of intent matching systems (e.g., converse, padatious_high, adapt, fallback).',
    'tooltip.transformers.audio': 'Plugins that modify raw audio before STT.',
    'tooltip.transformers.utterance': 'Plugins that modify transcribed text before intent parsing.',
    'tooltip.transformers.dialog': 'Plugins that modify the response text before TTS.',
    'tooltip.skills.auto_update': 'Automatically fetch updates from GitHub.',
    'tooltip.skills.blacklisted': 'Comma-separated list of skill IDs to ignore.',
    'tooltip.skills.priority': 'Skills that bypass normal confidence checks.',
    'tooltip.continuous.enabled': 'Keep listening after a response is spoken.',
    'tooltip.continuous.prompts': 'Optional prompts spoken to encourage the user to keep talking.',

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
    'settings.title': 'Administración de OVOS y Agentes',
    'settings.subtitle': 'Configuración integral para motores cognitivos autónomos.',
    'settings.advanced_mode': 'Editor JSON Avanzado',
    'settings.switch_ui': 'Cambiar a Interfaz',
    'settings.edit_json': 'Editar JSON Crudo',
    'settings.btn_apply': 'Aplicar al Clúster',
    'settings.btn_applying': 'Aplicando...',

    // Sidebar Tabs
    'tab.core': 'General y Ubicación',
    'tab.audio': 'Audio y Habla (STT/TTS)',
    'tab.plugins': 'Plugins (Activación/VAD)',
    'tab.pipeline': 'Tuberías de Intención',
    'tab.transformers': 'Transformadores',
    'tab.skills': 'Habilidades y Diálogo',

    // Core Tab
    'settings.lang': 'Idioma del Sistema',
    'settings.log_level': 'Nivel de Registro',
    'settings.location.city': 'Ciudad',
    'settings.location.timezone': 'Zona Horaria',
    'settings.gui.idle': 'Pantalla de Reposo',

    // Audio Tab
    'settings.tts': 'Motor de Texto-a-Voz',
    'settings.stt': 'Motor de Voz-a-Texto',

    // Plugins Tab
    'settings.wakeword.module': 'Motor de Palabra de Activación',
    'settings.wakeword.threshold': 'Umbral de Activación',
    'settings.vad.module': 'Módulo VAD',
    'settings.vad_energy': 'Energía VAD',

    // Pipeline Tab
    'settings.pipeline.order': 'Orden de Ejecución de Intenciones',

    // Transformers Tab
    'settings.transformers.audio': 'Transformadores de Audio',
    'settings.transformers.utterance': 'Transformadores de Expresión',
    'settings.transformers.dialog': 'Transformadores de Diálogo',

    // Skills Tab
    'settings.skills.auto_update': 'Actualizar Habilidades Auto',
    'settings.skills.blacklisted': 'Habilidades Bloqueadas',
    'settings.skills.priority': 'Habilidades Prioritarias',
    'settings.continuous.enabled': 'Conversación Continua',
    'settings.continuous.prompts': 'Mensajes de Seguimiento',

    // Tooltips
    'tooltip.lang': 'Código de idioma (ej., es-es).',
    'tooltip.log_level': 'Detalle de registros (DEBUG, INFO).',
    'tooltip.location.city': 'Ciudad física para clima y tiempo.',
    'tooltip.location.timezone': 'Zona horaria local.',
    'tooltip.gui.idle': 'Habilidad que se muestra en reposo.',
    'tooltip.tts': 'Motor para sintetizar audio.',
    'tooltip.stt': 'Motor para transcribir voz a texto.',
    'tooltip.wakeword.module': 'Motor que escucha la palabra clave.',
    'tooltip.wakeword.threshold': 'Sensibilidad a la palabra clave.',
    'tooltip.vad.module': 'Motor de detección de voz.',
    'tooltip.vad_energy': 'Valores altos reducen sensibilidad al ruido.',
    'tooltip.pipeline.order': 'Orden de coincidencia de intenciones (ej., converse, adapt).',
    'tooltip.transformers.audio': 'Modifica el audio antes del STT.',
    'tooltip.transformers.utterance': 'Modifica el texto antes de procesar la intención.',
    'tooltip.transformers.dialog': 'Modifica la respuesta antes de hablarla.',
    'tooltip.skills.auto_update': 'Obtiene actualizaciones de GitHub.',
    'tooltip.skills.blacklisted': 'IDs de habilidades ignoradas.',
    'tooltip.skills.priority': 'Habilidades con prioridad de respuesta.',
    'tooltip.continuous.enabled': 'Mantiene el micrófono abierto después de hablar.',
    'tooltip.continuous.prompts': 'Frases opcionales para incentivar a seguir hablando.',

    'cloning.title': 'Biblioteca de Clonación',
    'cloning.subtitle': 'Sube audios para clonar voces.',
    'cloning.clone_new': 'Clonar Voz',
    'cloning.voice_name': 'Nombre de Voz',
    'cloning.language': 'Idioma',
    'cloning.audio_sample': 'Muestra (WAV/MP3)',
    'cloning.btn_start': 'Iniciar',
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
