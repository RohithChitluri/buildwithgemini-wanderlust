import numpy as np
import scipy.io.wavfile as wavfile

sample_rate = 44100
bpm = 84
beat_duration = 60.0 / bpm
bar_duration = beat_duration * 4.0
total_duration = 72.0  # slightly longer than 68.5s demo

t = np.linspace(0, total_duration, int(sample_rate * total_duration), endpoint=False)
audio = np.zeros_like(t)

# Chords: Warm, jazzy Lo-Fi chord progression (e.g., Fmaj7 - Em7 - Dm7 - Cmaj7)
# Frequencies in Hz:
# Fmaj7: F3(174.61), A3(220.00), C4(261.63), E4(329.63)
# Em7:   E3(164.81), G3(196.00), B3(246.94), D4(293.66)
# Dm7:   D3(146.83), F3(174.61), A3(220.00), C4(261.63)
# Cmaj7: C3(130.81), E3(164.81), G3(196.00), B3(246.94)

chords = [
    [174.61, 220.00, 261.63, 329.63], # Fmaj7
    [164.81, 196.00, 246.94, 293.66], # Em7
    [146.83, 174.61, 220.00, 261.63], # Dm7
    [130.81, 164.81, 196.00, 246.94], # Cmaj7
]
bass_notes = [87.31, 82.41, 73.42, 65.41] # Bass octaves

# Synthesize Electric Piano / Rhodes chord pad with soft tremolo & low-pass warmth
num_bars = int(np.ceil(total_duration / bar_duration))
for bar in range(num_bars):
    chord_idx = bar % 4
    chord_freqs = chords[chord_idx]
    bass_freq = bass_notes[chord_idx]
    
    bar_start_t = bar * bar_duration
    bar_end_t = min((bar + 1) * bar_duration, total_duration)
    
    idx_start = int(bar_start_t * sample_rate)
    idx_end = int(bar_end_t * sample_rate)
    t_chunk = t[idx_start:idx_end] - bar_start_t
    
    # Soft envelope for Rhodes pad
    env = np.exp(-t_chunk * 0.45) * (1.0 - np.exp(-t_chunk * 15.0))
    
    # Pad sound (fundamental + warm 2nd harmonic + gentle chorus)
    pad = np.zeros_like(t_chunk)
    for f in chord_freqs:
        tremolo = 1.0 + 0.15 * np.sin(2 * np.pi * 3.5 * t_chunk)
        pad += 0.08 * np.sin(2 * np.pi * f * t_chunk) * tremolo
        pad += 0.03 * np.sin(2 * np.pi * (f * 2) * t_chunk) * tremolo
    
    # Warm sub-bass note
    bass_env = np.exp(-t_chunk * 0.7) * (1.0 - np.exp(-t_chunk * 25.0))
    bass = 0.22 * np.sin(2 * np.pi * bass_freq * t_chunk) * bass_env
    bass += 0.08 * np.sin(2 * np.pi * (bass_freq * 2) * t_chunk) * bass_env
    
    audio[idx_start:idx_end] += (pad * env) + bass

# Add upbeat, mellow Lo-Fi drum groove (Kick on 1 & 3-and, Snare on 2 & 4, Hi-hat on 8ths)
num_beats = int(total_duration / beat_duration)
for beat in range(num_beats):
    beat_t = beat * beat_duration
    beat_in_bar = beat % 4
    
    # 1. Soft Warm Lo-Fi Kick on beat 0 and beat 2.5 (upbeat bounce)
    def add_kick(kick_start_t):
        if kick_start_t + 0.25 > total_duration:
            return
        idx_s = int(kick_start_t * sample_rate)
        idx_e = min(idx_s + int(0.25 * sample_rate), len(audio))
        k_t = np.linspace(0, (idx_e - idx_s) / sample_rate, idx_e - idx_s, endpoint=False)
        # Pitch drop 120Hz -> 45Hz
        k_freq = 45.0 + 75.0 * np.exp(-k_t * 30.0)
        phase = 2 * np.pi * np.cumsum(k_freq) / sample_rate
        k_env = np.exp(-k_t * 14.0)
        audio[idx_s:idx_e] += 0.28 * np.sin(phase) * k_env

    if beat_in_bar == 0:
        add_kick(beat_t)
    elif beat_in_bar == 2:
        add_kick(beat_t)
        add_kick(beat_t + beat_duration * 0.5)

    # 2. Snare / Rimshot on beats 1 and 3 (classic 2 & 4)
    if beat_in_bar in (1, 3):
        idx_s = int(beat_t * sample_rate)
        idx_e = min(idx_s + int(0.18 * sample_rate), len(audio))
        s_t = np.linspace(0, (idx_e - idx_s) / sample_rate, idx_e - idx_s, endpoint=False)
        # Noise burst + tone body
        noise = (np.random.rand(len(s_t)) * 2 - 1) * np.exp(-s_t * 28.0)
        tone = np.sin(2 * np.pi * 180.0 * s_t) * np.exp(-s_t * 22.0)
        audio[idx_s:idx_e] += 0.16 * (noise * 0.7 + tone * 0.3)

    # 3. Lo-Fi closed Hi-Hat on 8th notes (swing feel)
    for eighth in [0.0, 0.52]: # gentle swing
        h_t = beat_t + eighth * beat_duration
        if h_t + 0.06 > total_duration:
            continue
        idx_s = int(h_t * sample_rate)
        idx_e = min(idx_s + int(0.06 * sample_rate), len(audio))
        hat_t = np.linspace(0, (idx_e - idx_s) / sample_rate, idx_e - idx_s, endpoint=False)
        hat_noise = (np.random.rand(len(hat_t)) * 2 - 1) * np.exp(-hat_t * 70.0)
        accent = 0.09 if eighth == 0.0 else 0.06
        audio[idx_s:idx_e] += accent * hat_noise

# Add light vinyl crackle / lo-fi texture
vinyl = (np.random.rand(len(t)) * 2 - 1) * 0.008
# Occasional soft clicks
pop_indices = np.random.choice(len(t), size=int(total_duration * 3), replace=False)
vinyl[pop_indices] += np.random.uniform(-0.04, 0.04, size=len(pop_indices))
audio += vinyl

# Fade in and fade out
fade_in = int(2.0 * sample_rate)
fade_out = int(3.0 * sample_rate)
audio[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
audio[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)

# Normalize
audio = audio / (np.max(np.abs(audio)) + 1e-6) * 0.75

wavfile.write("/config/Desktop/BuildWithGemini/lofi_beat.wav", sample_rate, (audio * 32767).astype(np.int16))
print("Lo-Fi beat generated successfully at /config/Desktop/BuildWithGemini/lofi_beat.wav!")
