import numpy as np
import random

def extrair(landmarks):
    pontos = np.array([[lm['x'], lm['y'], lm['z']] for lm in landmarks])
    olho_esq, olho_dir, nariz = pontos[33], pontos[263], pontos[1]
    dist_olhos = np.linalg.norm(olho_esq - olho_dir)
    if dist_olhos == 0: dist_olhos = 1e-6
    distancias = np.linalg.norm(pontos - nariz, axis=1) / dist_olhos
    distancias = distancias - distancias.mean()
    passo = max(1, len(distancias) // 128)
    vetor = distancias[::passo][:128]
    if len(vetor) < 128:
        vetor = np.pad(vetor, (0, 128 - len(vetor)))
    norma = np.linalg.norm(vetor)
    return vetor / norma if norma > 0 else vetor

def sim(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

base_rosto = [{'x': 0.5 + 0.1 * np.cos(i), 'y': 0.5 + 0.1 * np.sin(i), 'z': 0.05 * np.cos(i*2)} for i in range(478)]

# Pessoa 1 (olhos mais separados)
p1 = [{'x': p['x'] + random.uniform(-0.005, 0.005), 'y': p['y'] + random.uniform(-0.005, 0.005), 'z': p['z']} for p in base_rosto]
p1[33]['x'] -= 0.02
p1[263]['x'] += 0.02
v1 = extrair(p1)

# Pessoa 2 (nariz mais longo)
p2 = [{'x': p['x'] + random.uniform(-0.005, 0.005), 'y': p['y'] + random.uniform(-0.005, 0.005), 'z': p['z']} for p in base_rosto]
p2[1]['y'] += 0.03
v2 = extrair(p2)

# P1 com ruído de movimento
p1_v = [{'x': p['x'] + random.uniform(-0.002, 0.002), 'y': p['y'] + random.uniform(-0.002, 0.002), 'z': p['z']} for p in p1]
v1_v = extrair(p1_v)

print("Similaridade P1 e P1_v:", sim(v1, v1_v))
print("Similaridade P1 e P2:", sim(v1, v2))
