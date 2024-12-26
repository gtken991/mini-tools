"""Speech to Text Converter"""

import json
import logging
from pathlib import Path
from typing import List, Optional
import speech_recognition as sr
from dataclasses import dataclass
from pydub import AudioSegment
import shutil
import sys
import whisper  # Added import for whisper

logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    if not shutil.which('ffmpeg'):
        logger.error("ffmpeg not found. Please install ffmpeg first.")
        logger.error("Ubuntu/Debian: sudo apt-get install ffmpeg")
        logger.error("macOS: brew install ffmpeg")
        logger.error("Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

@dataclass
class AudioInfo:
    """Data class for storing audio file information"""
    path: Path
    duration: float
    channels: int
    sample_width: int
    framerate: int

class BaseProvider:
    """Base class for speech recognition providers"""
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.recognizer = sr.Recognizer()
    
    def convert(self, audio_data) -> Optional[str]:
        """Convert audio to text"""
        raise NotImplementedError

class LocalProvider(BaseProvider):
    """Local speech recognition using pocketsphinx"""
    def convert(self, audio_data) -> Optional[str]:
        try:
            return self.recognizer.recognize_sphinx(audio_data)
        except sr.UnknownValueError:
            logger.error("Sphinx could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Sphinx error; {e}")
            logger.error("Please ensure pocketsphinx is installed correctly")
            return None

class CloudProvider(BaseProvider):
    """Cloud-based speech recognition (Google)"""
    def convert(self, audio_data) -> Optional[str]:
        provider = self.credentials.get('provider')
        try:
            if provider == 'google':
                language = self.credentials.get('language', 'en-US')
                return self.recognizer.recognize_google(
                    audio_data,
                    language=language
                )
            elif provider == 'whisper':
                # Get Whisper settings
                model_name = self.credentials.get('model', 'base')
                language = self.credentials.get('language')
                
                # Load Whisper model
                model = whisper.load_model(model_name)
                
                # Convert audio data to file
                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                temp_file = temp_dir / "temp_audio.wav"
                
                with open(temp_file, 'wb') as f:
                    f.write(audio_data.get_wav_data())
                
                try:
                    # Transcribe using Whisper
                    result = model.transcribe(
                        str(temp_file),
                        language=language,
                        task="transcribe"
                    )
                    return result["text"]
                finally:
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()
                        
        except Exception as e:
            logger.error(f"Error with {provider} API: {str(e)}")
            return None

class WhisperProvider(BaseProvider):
    """Direct Whisper API provider"""
    def __init__(self, credentials: dict, model_dir: Path):
        self.credentials = credentials
        self.model_dir = model_dir
        
        # Ensure model directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Get model configuration
        model_name = credentials.get('model', 'base')
        update_model = credentials.get('update_model', False)
        model_path = self.model_dir / f"{model_name}.pt"
        
        # Check if model file exists
        if not model_path.exists():
            logger.info(f"Downloading Whisper {model_name} model (this may take a while)...")
            logger.info(f"Model will be saved at: {model_path}")
            logger.info("Model sizes: tiny=39M, base=74M, small=244M, medium=769M, large=1550M")
            
            # Download and save model
            self.model = whisper.load_model(
                model_name,
                download_root=str(self.model_dir)
            )
            logger.info("Model downloaded successfully!")
        else:
            if update_model:
                logger.info(f"Updating Whisper {model_name} model...")
                self.model = whisper.load_model(
                    model_name,
                    download_root=str(self.model_dir)
                )
                logger.info("Model updated successfully!")
            else:
                logger.info(f"Loading existing model from: {model_path}")
                self.model = whisper.load_model(
                    model_name,
                    download_root=str(self.model_dir)
                )
    
    def convert(self, audio_data) -> Optional[str]:
        """Convert audio to text using Whisper"""
        try:
            # Create temp directory if not exists
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Save audio data to temporary file
            temp_file = temp_dir / "temp_whisper.wav"
            with open(temp_file, 'wb') as f:
                f.write(audio_data.get_wav_data())
            
            try:
                # Transcribe using Whisper
                result = self.model.transcribe(
                    str(temp_file),
                    language=self.credentials.get('language'),
                    task="transcribe"
                )
                return result["text"]
            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                    
        except Exception as e:
            logger.error(f"Error with Whisper API: {str(e)}")
            return None

class SpeechToText:
    """Main class for speech to text conversion"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration"""
        check_ffmpeg()
        
        self.config = self._load_config(config_path)
        self.input_dir = Path(self.config['input_directory']).expanduser()
        self.output_dir = Path(self.config['output_directory']).expanduser()
        
        # Set up logging
        self._setup_logging(
            level=self.config['logging']['level'],
            log_file=self.config['logging']['file']
        )
        
        # Initialize provider
        self.provider = self._setup_provider()
        self.recognizer = sr.Recognizer()
    
    def _setup_provider(self) -> BaseProvider:
        """Set up speech recognition provider"""
        provider_type = self.config['api_settings']['provider']
        credentials = self.config['api_settings']['credentials']
        
        if provider_type == 'local':
            return LocalProvider(credentials)
        elif provider_type == 'whisper':
            model_dir = Path(self.config.get('model_directory', './models'))
            return WhisperProvider(credentials[provider_type], model_dir)
        else:
            credentials['provider'] = provider_type
            return CloudProvider(credentials)
    
    def _load_config(self, config_path: str) -> dict:
        """Load and validate configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_fields = [
                'input_directory',
                'output_directory',
                'api_settings',
                'file_types',
                'output_format',
                'logging'
            ]
            
            for field in required_fields:
                if field not in config:
                    raise KeyError(f"Missing required field: {field}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise
    
    def _setup_logging(self, level: str, log_file: str):
        """Configure logging"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_audio_info(self, file_path: Path) -> Optional[AudioInfo]:
        """Get audio file information for any supported format"""
        try:
            # Load audio file using pydub
            audio = AudioSegment.from_file(str(file_path))
            
            return AudioInfo(
                path=file_path,
                duration=len(audio) / 1000.0,  # Convert milliseconds to seconds
                channels=audio.channels,
                sample_width=audio.sample_width,
                framerate=audio.frame_rate
            )
            
        except Exception as e:
            logger.error(f"Error reading audio file {file_path}: {str(e)}")
            return None
    
    def scan_files(self) -> List[Path]:
        """Scan input directory for audio files"""
        files = []
        for file_type in self.config['file_types']:
            files.extend(self.input_dir.glob(f"*{file_type}"))
        return files
    
    def convert_audio_to_wav(self, file_path: Path) -> Optional[str]:
        """Convert any audio format to WAV for processing"""
        try:
            # Create temporary directory if it doesn't exist
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate temporary WAV file path
            temp_wav = temp_dir / f"{file_path.stem}_temp.wav"
            
            # Load and export as WAV
            audio = AudioSegment.from_file(str(file_path))
            audio.export(str(temp_wav), format="wav")
            
            return str(temp_wav)
            
        except Exception as e:
            logger.error(f"Error converting {file_path} to WAV: {str(e)}")
            return None
    
    def split_audio(self, audio_path: Path, segment_length: int = 60) -> List[Path]:
        """Split audio into smaller segments"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(str(audio_path))
            
            # Convert to mono and reduce quality to decrease file size
            audio = audio.set_channels(1)  # Convert to mono
            audio = audio.set_frame_rate(16000)  # Reduce sample rate
            
            # Create temp directory for segments
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Split audio into segments
            segments = []
            for i, start in enumerate(range(0, len(audio), segment_length * 1000)):
                # Extract segment
                end = start + segment_length * 1000
                segment = audio[start:end]
                
                # Save segment with compression
                segment_path = temp_dir / f"{audio_path.stem}_segment_{i}.wav"
                segment.export(
                    str(segment_path),
                    format="wav",
                    parameters=[
                        "-ac", "1",  # mono
                        "-ar", "16000",  # 16kHz sample rate
                        "-ab", "32k",  # 32kbps bitrate
                    ]
                )
                segments.append(segment_path)
                
            return segments
            
        except Exception as e:
            logger.error(f"Error splitting audio {audio_path}: {str(e)}")
            return []
    
    def convert_audio(self, audio_path: Path) -> Optional[str]:
        """Convert audio to text using configured provider"""
        try:
            # Convert to WAV if not already
            if audio_path.suffix.lower() != '.wav':
                temp_wav = self.convert_audio_to_wav(audio_path)
                if not temp_wav:
                    return None
                audio_path = Path(temp_wav)
            
            with sr.AudioFile(str(audio_path)) as source:
                audio = self.recognizer.record(source)
                return self.provider.convert(audio)
                
        except Exception as e:
            logger.error(f"Error converting {audio_path}: {str(e)}")
            return None
        finally:
            # Clean up temporary WAV file if it was created
            if str(audio_path).startswith('temp/'):
                try:
                    audio_path.unlink()
                except Exception:
                    pass
    
    def save_transcript(self, text: str, audio_path: Path):
        """Save transcript to file"""
        try:
            output_format = self.config['output_format']['type']
            output_path = self.output_dir / f"{audio_path.stem}.{output_format}"
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
            logger.info(f"Saved transcript to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
    
    def process_files(self):
        """Process all audio files"""
        files = self.scan_files()
        logger.info(f"Found {len(files)} audio files")
        
        for file_path in files:
            logger.info(f"Processing {file_path}")
            
            # Get audio information
            audio_info = self.get_audio_info(file_path)
            if not audio_info:
                continue
            
            # Convert to text
            text = self.convert_audio(file_path)
            if not text:
                continue
            
            # Save transcript
            self.save_transcript(text, file_path)

def main():
    """Main function"""
    try:
        converter = SpeechToText()
        converter.process_files()
        logger.info("Speech to text conversion completed")
        return 0
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main()) 