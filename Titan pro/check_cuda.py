import numpy as np
import pyopencl as cl
import time
import threading
import matplotlib.pyplot as plt
import warnings

# Ignorar avisos comuns do PyOpenCL para um output mais limpo
warnings.filterwarnings("ignore", category=cl.CompilerWarning)
warnings.filterwarnings("ignore", category=cl.RepeatedKernelRetrieval)

# --- Parâmetros do Teste ---
NUM_TESTS = 30000
MATRIX_SIZE = 128

# --- Kernel OpenCL (A "instrução" que a GPU vai executar repetidamente) ---
KERNEL_CODE = """
__kernel void matmul(__global const float* A, __global const float* B, __global float* C) {
    int i = get_global_id(0);
    int j = get_global_id(1);
    float sum = 0.0f;
    for (int k = 0; k < """ + str(MATRIX_SIZE) + """; k++) {
        sum += A[i * """ + str(MATRIX_SIZE) + """ + k] * B[k * """ + str(MATRIX_SIZE) + """ + j];
    }
    C[i * """ + str(MATRIX_SIZE) + """ + j] = sum;
}
"""

# =============================================================================
# FUNÇÕES DE EXECUÇÃO
# =============================================================================

def find_devices():
    """Encontra e retorna os dispositivos de GPU da Intel and NVIDIA."""
    intel_device, nvidia_device = None, None
    print("Procurando dispositivos de GPU...")
    try:
        for platform in cl.get_platforms():
            if 'Intel' in platform.name and not intel_device:
                intel_devices = platform.get_devices(device_type=cl.device_type.GPU)
                if intel_devices:
                    intel_device = intel_devices[0]
                    print(f"  [✓] Encontrado: {intel_device.name}")
            if 'NVIDIA' in platform.name and not nvidia_device:
                nvidia_devices = platform.get_devices(device_type=cl.device_type.GPU)
                if nvidia_devices:
                    nvidia_device = nvidia_devices[0]
                    print(f"  [✓] Encontrado: {nvidia_device.name}")
    except Exception as e:
        print(f"ERRO ao procurar dispositivos: {e}")
    return intel_device, nvidia_device

def opencl_worker(device, num_tests_for_worker):
    """Função que roda uma carga de trabalho em um dispositivo OpenCL específico."""
    try:
        context = cl.Context([device])
        queue = cl.CommandQueue(context)
        prg = cl.Program(context, KERNEL_CODE).build()

        a_np = np.random.rand(MATRIX_SIZE, MATRIX_SIZE).astype(np.float32)
        b_np = np.random.rand(MATRIX_SIZE, MATRIX_SIZE).astype(np.float32)
        c_np = np.empty_like(a_np)

        mf = cl.mem_flags
        a_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a_np)
        b_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b_np)
        c_g = cl.Buffer(context, mf.WRITE_ONLY, c_np.nbytes)

        for _ in range(num_tests_for_worker):
            prg.matmul(queue, (MATRIX_SIZE, MATRIX_SIZE), None, a_g, b_g, c_g)
        
        queue.finish() # Garante que todos os cálculos terminaram
    except Exception as e:
        print(f"ERRO no worker da GPU {device.name}: {e}")


# =============================================================================
# MAIN - ORQUESTRADOR DO BENCHMARK
# =============================================================================
if __name__ == '__main__':
    intel_gpu, nvidia_gpu = find_devices()
    
    if not intel_gpu or not nvidia_gpu:
        print("\n❌ ERRO: Não foi possível encontrar as duas GPUs (Intel e NVIDIA). O benchmark não pode continuar.")
        exit()

    results = {}

    # --- Teste 1: Somente Intel ---
    print(f"\n--- TESTE 1: Rodando {NUM_TESTS} operações somente na GPU Intel ---")
    start_time = time.time()
    opencl_worker(intel_gpu, NUM_TESTS)
    end_time = time.time()
    results['Intel GPU (Sozinha)'] = end_time - start_time
    print(f"⏱️  Tempo: {results['Intel GPU (Sozinha)']:.4f} segundos")

    # --- Teste 2: Somente NVIDIA ---
    print(f"\n--- TESTE 2: Rodando {NUM_TESTS} operações somente na GPU NVIDIA ---")
    start_time = time.time()
    opencl_worker(nvidia_gpu, NUM_TESTS)
    end_time = time.time()
    results['NVIDIA GPU (Sozinha)'] = end_time - start_time
    print(f"⏱️  Tempo: {results['NVIDIA GPU (Sozinha)']:.4f} segundos")

    # --- Teste 3: Ambas em Paralelo ---
    print("\n--- TESTE 3: Rodando operações com ambas as GPUs em paralelo ---")
    
    # Divisão de carga (70% para a NVIDIA, 30% para a Intel)
    nvidia_load = int(NUM_TESTS * 0.7)
    intel_load = NUM_TESTS - nvidia_load
    print(f"Divisão de carga: NVIDIA fará {nvidia_load} ops, Intel fará {intel_load} ops.")

    thread_intel = threading.Thread(target=opencl_worker, args=(intel_gpu, intel_load))
    thread_nvidia = threading.Thread(target=opencl_worker, args=(nvidia_gpu, nvidia_load))

    start_time = time.time()
    thread_intel.start()
    thread_nvidia.start()
    thread_intel.join()
    thread_nvidia.join()
    end_time = time.time()
    results['Intel + NVIDIA (Juntas)'] = end_time - start_time
    print(f"⏱️  Tempo Total: {results['Intel + NVIDIA (Juntas)']:.4f} segundos")

    # --- Apresentação dos Resultados ---
    print("\n" + "="*30)
    print("--- RESULTADO FINAL DO BENCHMARK ---")
    print("="*30)
    for name, t in results.items():
        print(f"{name:<25}: {t:.4f} segundos")
    
    # Gerar Gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = list(results.keys())
    times = list(results.values())
    bars = ax.bar(labels, times, color=['#5B9BD5', '#ED7D31', '#70AD47'])
    ax.set_ylabel('Tempo de Execução (segundos)')
    ax.set_title(f'Benchmark de Performance de GPU ({NUM_TESTS} Operações)')
    ax.bar_label(bars, fmt='%.2fs')
    
    plt.tight_layout()
    print("\nGerando gráfico de resultados...")
    plt.show()