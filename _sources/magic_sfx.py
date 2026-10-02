# Synthesizes the "magic" sound played when the envelope opens -> assets/magic.wav
import numpy as np, wave

SR = 44100
DUR = 3.2
rng = np.random.default_rng(7)
t = np.arange(int(SR * DUR)) / SR
L = np.zeros_like(t); R = np.zeros_like(t)

def add(sig, start, pan):
    i = int(start * SR); n = min(len(sig), len(t) - i)
    L[i:i+n] += sig[:n] * np.cos(pan * np.pi / 2)
    R[i:i+n] += sig[:n] * np.sin(pan * np.pi / 2)

def bell(f, dur, decay, amp):
    x = np.arange(int(SR * dur)) / SR
    env = np.exp(-x / decay) * np.minimum(1, x / 0.004)
    tone = (np.sin(2*np.pi*f*x) + .35*np.sin(2*np.pi*2*f*x) * np.exp(-x/(decay*.4))
            + .18*np.sin(2*np.pi*2.76*f*x) * np.exp(-x/(decay*.25)))
    return amp * env * tone

# Rising harp/celesta glissando on a major pentatonic scale
pent = [0, 2, 4, 7, 9]
notes = [523.25 * 2 ** ((12*o + s) / 12) for o in range(3) for s in pent][:14]
for k, f in enumerate(notes):
    add(bell(f, 2.2, 0.9 - k*0.03, 0.22), 0.05 + k * 0.065, 0.25 + 0.5 * k / len(notes))

# Final shimmering chord
for f in (1046.5, 1318.5, 1568.0, 2093.0):
    add(bell(f, 2.5, 1.1, 0.12), 1.0, rng.uniform(.3, .7))

# Random fairy-dust sparkles
for _ in range(40):
    add(bell(rng.uniform(2500, 6500), 0.5, rng.uniform(.06, .18), rng.uniform(.03, .08)),
        rng.uniform(0.15, 2.2), rng.uniform(0, 1))

# Soft airy whoosh swelling under the glissando
noise = rng.standard_normal(len(t))
k = np.ones(40) / 40
air = noise - np.convolve(noise, k, "same")            # crude high-pass
swell = np.exp(-((t - 0.8) / 0.45) ** 2) * 0.05
L += air * swell; R += np.roll(air, 300) * swell

# Reverb: convolve with a decaying noise impulse response
ir_t = np.arange(int(SR * 1.6)) / SR
def verb(x, seed):
    ir = np.random.default_rng(seed).standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45)
    ir[0] = 0
    n = len(x) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)]
    return x * 0.75 + wet / np.abs(wet).max() * np.abs(x).max() * 0.35
L, R = verb(L, 1), verb(R, 2)

fade = np.minimum(1, (DUR - t) / 0.6)
out = np.stack([L, R], 1) * fade[:, None]
out = out / np.abs(out).max() * 0.85
with wave.open("assets/magic.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
