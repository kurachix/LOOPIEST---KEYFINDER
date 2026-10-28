"""
LOOPIEST DOWNLOADER - Engine de Extração e Conversão de Áudio Multi-Provedor.
Suporta YouTube, SoundCloud, TikTok, Instagram, Bandcamp, X/Twitter, Mixcloud e +1000 provedores via yt-dlp.
Realiza conversão em alta definição (MP3 320kbps / 192kbps e WAV Studio 44.1kHz) via FFmpeg embutido.
"""

import os
import re
import shutil
import subprocess
from typing import Dict, Any, Callable, Optional
from urllib.parse import urlparse


# Provedores famosos reconhecidos visualmente na interface
PROVIDER_MAP = {
    "youtube.com": ("YOUTUBE", "#FF0033"),
    "youtu.be": ("YOUTUBE", "#FF0033"),
    "music.youtube.com": ("YOUTUBE MUSIC", "#FF0033"),
    "soundcloud.com": ("SOUNDCLOUD", "#FF5500"),
    "on.soundcloud.com": ("SOUNDCLOUD", "#FF5500"),
    "tiktok.com": ("TIKTOK", "#00F2FE"),
    "instagram.com": ("INSTAGRAM", "#E1306C"),
    "bandcamp.com": ("BANDCAMP", "#1DA0C3"),
    "twitter.com": ("X / TWITTER", "#1DA1F2"),
    "x.com": ("X / TWITTER", "#1DA1F2"),
    "mixcloud.com": ("MIXCLOUD", "#5000FF"),
    "vimeo.com": ("VIMEO", "#1AB7EA"),
    "twitch.tv": ("TWITCH", "#9146FF"),
    "facebook.com": ("FACEBOOK", "#1877F2"),
    "fb.watch": ("FACEBOOK", "#1877F2"),
}


def detectar_provedor(url: str) -> Dict[str, str]:
    """
    Identifica o provedor a partir da URL informada para exibição de badge na UI.
    """
    if not url or not url.strip():
        return {"name": "AGUARDANDO LINK", "color": "#8E8EA0", "domain": ""}

    texto = url.strip()
    if not texto.startswith(("http://", "https://")):
        texto = "https://" + texto

    try:
        parsed = urlparse(texto)
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain.startswith("m."):
            domain = domain[2:]

        for key_domain, (prov_name, prov_color) in PROVIDER_MAP.items():
            if domain == key_domain or domain.endswith("." + key_domain):
                return {"name": prov_name, "color": prov_color, "domain": domain}

        if "." in domain and len(domain) >= 4:
            clean_host = domain.split(".")[0].upper()
            return {"name": f"{clean_host} STREAM", "color": "#B066FE", "domain": domain}
    except Exception:
        pass

    return {"name": "LINK INVÁLIDO", "color": "#EF4444", "domain": ""}


def validar_url_download(url: str) -> bool:
    """Valida se a string informada possui estrutura de URL HTTP/HTTPS válida."""
    if not url or not isinstance(url, str):
        return False
    texto = url.strip()
    if not texto.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(texto)
        return bool(parsed.netloc and "." in parsed.netloc)
    except Exception:
        return False


def sanitizar_nome_arquivo(titulo: str) -> str:
    """Remove caracteres inválidos do Windows para nomes de arquivos."""
    if not titulo:
        return "Loopiest_Audio_Track"
    limpo = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", titulo)
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    return limpo[:140] if limpo else "Loopiest_Audio_Track"


def localizar_ffmpeg() -> Optional[str]:
    """
    Localiza o binário do FFmpeg priorizando o pacote embutido imageio-ffmpeg
    e usando o PATH do sistema como fallback.
    """
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.exists(ffmpeg_exe):
            return ffmpeg_exe
    except Exception:
        pass

    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg and os.path.exists(sys_ffmpeg):
        return sys_ffmpeg

    return None


def obter_pasta_padrao_downloads() -> str:
    """Retorna a pasta padrão de Downloads do usuário no Windows."""
    user_profile = os.path.expanduser("~")
    downloads_dir = os.path.join(user_profile, "Downloads", "LOOPIEST_DOWNLOADS")
    try:
        os.makedirs(downloads_dir, exist_ok=True)
        return downloads_dir
    except Exception:
        fallback = os.path.join(user_profile, "Downloads")
        return fallback if os.path.exists(fallback) else user_profile


def baixar_e_converter_audio(
    url: str,
    pasta_destino: str,
    formato_qualidade: str = "mp3_320",
    auto_keyfinder: bool = False,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None
) -> Dict[str, Any]:
    """
    Realiza o download da melhor stream de áudio do provedor (YouTube, SoundCloud, etc.)
    e converte para MP3 (320kbps / 192kbps) ou WAV (44.1kHz 16-bit) usando FFmpeg.
    Opcionalmente executa a análise tonal (BPM + Key) e renomeia o arquivo final.
    """
    if not validar_url_download(url):
        raise ValueError("URL inválida. Insira um link completo começando com https://")

    os.makedirs(pasta_destino, exist_ok=True)

    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("Biblioteca 'yt-dlp' não encontrada no ambiente.") from exc

    ffmpeg_exe = localizar_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError("Motor de conversão FFmpeg não encontrado no sistema.")

    def emitir_progresso(pct: int, msg: str):
        if progress_callback:
            progress_callback(max(0, min(100, int(pct))), msg)

    def verificar_cancelamento():
        if cancel_check and cancel_check():
            raise InterruptedError("Download cancelado pelo usuário.")

    provedor_info = detectar_provedor(url)
    emitir_progresso(5, f"Conectando ao provedor ({provedor_info['name']})...")
    verificar_cancelamento()

    # Hook de progresso em tempo real do yt-dlp
    def ytdlp_hook(d: Dict[str, Any]):
        verificar_cancelamento()
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed") or 0

            if total > 0:
                raw_pct = (downloaded / total) * 100.0
                scaled_pct = 10 + int(raw_pct * 0.65)  # 10% a 75%
            else:
                scaled_pct = 40

            if speed and speed > 0:
                speed_mb = speed / (1024 * 1024)
                emitir_progresso(scaled_pct, f"Baixando stream de áudio... ({speed_mb:.1f} MB/s)")
            else:
                emitir_progresso(scaled_pct, "Baixando stream de áudio em alta qualidade...")
        elif status == "finished":
            emitir_progresso(76, "Stream recebida! Preparando conversão de estúdio...")

    # Template temporário seguro dentro da pasta de destino
    temp_prefix = os.path.join(pasta_destino, "_loopiest_temp_%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": temp_prefix,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "progress_hooks": [ytdlp_hook],
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }

    temp_downloaded_file = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            emitir_progresso(10, "Extraindo informações da faixa e stream de áudio...")
            info = ydl.extract_info(url.strip(), download=True)

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            temp_downloaded_file = ydl.prepare_filename(info)
            if not os.path.exists(temp_downloaded_file):
                # Fallback caso a extensão real tenha mudado
                video_id = info.get("id", "")
                for fname in os.listdir(pasta_destino):
                    if fname.startswith(f"_loopiest_temp_{video_id}"):
                        temp_downloaded_file = os.path.join(pasta_destino, fname)
                        break

        verificar_cancelamento()

        if not temp_downloaded_file or not os.path.exists(temp_downloaded_file):
            raise RuntimeError("Não foi possível localizar o stream de áudio baixado.")

        raw_title = info.get("title") or "Loopiest Track"
        uploader = info.get("uploader") or info.get("artist") or info.get("channel") or "Desconhecido"
        duration_sec = float(info.get("duration") or 0.0)
        extractor_name = (info.get("extractor_key") or provedor_info["name"]).upper()

        clean_title = sanitizar_nome_arquivo(raw_title)

        # Define extensão e parâmetros de codificação FFmpeg
        if formato_qualidade == "wav":
            ext_final = ".wav"
            codec_args = ["-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2"]
            quality_label = "WAV Studio 44.1kHz 16-bit"
        elif formato_qualidade == "mp3_192":
            ext_final = ".mp3"
            codec_args = ["-vn", "-acodec", "libmp3lame", "-ab", "192k", "-ar", "44100", "-ac", "2"]
            quality_label = "MP3 192 kbps"
        else:
            ext_final = ".mp3"
            codec_args = ["-vn", "-acodec", "libmp3lame", "-ab", "320k", "-ar", "44100", "-ac", "2"]
            quality_label = "MP3 320 kbps Extreme"

        output_path = os.path.join(pasta_destino, f"{clean_title}{ext_final}")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(pasta_destino, f"{clean_title} ({counter}){ext_final}")
            counter += 1

        emitir_progresso(80, f"Convertendo para {quality_label}...")

        ffmpeg_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", temp_downloaded_file,
            *codec_args,
            "-metadata", f"title={raw_title}",
            "-metadata", f"artist={uploader}",
            "-metadata", "comment=Downloaded via LOOPIEST SUITE",
            output_path
        ]

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags
        )

        if proc.returncode != 0 or not os.path.exists(output_path):
            err_msg = proc.stderr.decode("utf-8", errors="ignore")[-300:]
            raise RuntimeError(f"Falha na conversão FFmpeg: {err_msg}")

        # Remove arquivo temporário bruto
        try:
            if os.path.exists(temp_downloaded_file):
                os.remove(temp_downloaded_file)
        except Exception:
            pass

        resultado = {
            "title": raw_title,
            "uploader": uploader,
            "provider": provedor_info["name"] if provedor_info["name"] != "AGUARDANDO LINK" else extractor_name,
            "duration_sec": duration_sec,
            "file_path": output_path,
            "file_name": os.path.basename(output_path),
            "quality_label": quality_label,
            "bpm": None,
            "key": None,
            "relative_key": None,
        }

        # Se o produtor ativou a integração automática com o KeyFinder (BPM + Tom)
        if auto_keyfinder:
            verificar_cancelamento()
            emitir_progresso(90, "Detectando BPM e Tonalidade (Motor KeyFinder)...")
            try:
                from src.audio_analyzer import carregar_audio, calcular_bpm, ranquear_notas_em_memoria
                from src.key_detector import descobrir_tom, obter_escala_relativa

                y, sr = carregar_audio(output_path)
                if duration_sec <= 0:
                    duration_sec = round(len(y) / float(sr), 2)
                    resultado["duration_sec"] = duration_sec

                bpm = calcular_bpm(y, sr)
                ranking = ranquear_notas_em_memoria(y, sr, top_n=8)
                key_str, _ = descobrir_tom(ranking, detalhado=True)
                detected_key = key_str.replace("Key: ", "")
                rel_key = obter_escala_relativa(detected_key)

                resultado["bpm"] = bpm
                resultado["key"] = detected_key
                resultado["relative_key"] = rel_key

                # Renomeia o arquivo incluindo BPM e Tom automaticamente
                stem, ext = os.path.splitext(output_path)
                tagged_path = f"{stem} - {bpm}bpm {detected_key}{ext}"
                if not os.path.exists(tagged_path):
                    os.rename(output_path, tagged_path)
                    resultado["file_path"] = tagged_path
                    resultado["file_name"] = os.path.basename(tagged_path)
            except Exception as kf_err:
                print(f"[Aviso Auto-KeyFinder]: {kf_err}")

        emitir_progresso(100, "Download e conversão concluídos com sucesso!")
        return resultado

    finally:
        if temp_downloaded_file and os.path.exists(temp_downloaded_file):
            try:
                os.remove(temp_downloaded_file)
            except Exception:
                pass

