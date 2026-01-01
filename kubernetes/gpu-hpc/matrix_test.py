import tensorflow as tf
import numpy as np
import time

print("TensorFlow version:", tf.__version__)
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

# GPU matrix multiplication with TensorFlow
if len(tf.config.list_physical_devices('GPU')) > 0:
    print("\nRunning GPU-accelerated TensorFlow matrix op...")
    with tf.device('/GPU:0'):
        n = 4096
        a = tf.random.normal([n, n])
        b = tf.random.normal([n, n])
        start = time.time()
        c = tf.matmul(a, b)
        tf.print("GPU matmul result shape:", c.shape)
        print(f"GPU time: {time.time() - start:.2f}s")
else:
    print("\nNo GPU detected - falling back to CPU")

    # CPU fallback with NumPy
    print("\nCPU NumPy matrix multiplication...")
    n_np = 2000
    a_np = np.random.rand(n_np, n_np)
    b_np = np.random.rand(n_np, n_np)
    start_np = time.time()
    c_np = np.matmul(a_np, b_np)
    print("NumPy result shape:", c_np.shape)
    print(f"CPU time: {time.time() - start_np:.2f}s")
