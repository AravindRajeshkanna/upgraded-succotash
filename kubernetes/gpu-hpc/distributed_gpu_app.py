import os
import time
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torch.nn.parallel import DistributedDataParallel as DDP


def setup_distributed(backend="nccl"):
    """
    Initialize torch.distributed using environment variables
    commonly set by MPI or Kubernetes launchers:
      - RANK / WORLD_SIZE / LOCAL_RANK
    """
    rank = int(os.environ.get("RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", rank))  # fallback

    torch.cuda.set_device(local_rank)
    dist.init_process_group(
        backend=backend,
        init_method="env://",
        rank=rank,
        world_size=world_size,
    )
    return rank, world_size, local_rank


class ToyModel(nn.Module):
    """Simple linear model for demo purposes."""
    def __init__(self, input_dim=1024, hidden_dim=1024, output_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


def synthetic_data(batch_size, input_dim, num_batches):
    """Yield random batches to simulate a dataset."""
    for _ in range(num_batches):
        x = torch.randn(batch_size, input_dim, device="cuda")
        y = torch.randint(0, 10, (batch_size,), device="cuda")
        yield x, y


def main():
    rank, world_size, local_rank = setup_distributed(backend="nccl")

    # Hyperparameters
    input_dim = 1024
    hidden_dim = 1024
    output_dim = 10
    batch_size = 128
    num_batches = 50
    lr = 1e-3

    # Model, loss, optimizer
    model = ToyModel(input_dim, hidden_dim, output_dim).cuda()
    ddp_model = DDP(model, device_ids=[local_rank], output_device=local_rank)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(ddp_model.parameters(), lr=lr)

    # Optional: each rank writes to shared storage (e.g., NFS)
    output_dir = os.environ.get("OUTPUT_DIR", "/shared/results")
    if rank == 0:
        os.makedirs(output_dir, exist_ok=True)

    dist.barrier()
    if rank == 0:
        print(f"World size: {world_size}, starting training...")

    start = time.time()
    for step, (x, y) in enumerate(synthetic_data(batch_size, input_dim, num_batches), start=1):
        optimizer.zero_grad()
        logits = ddp_model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()

        # Optionally log from rank 0 only
        if rank == 0 and step % 10 == 0:
            print(f"[step {step}/{num_batches}] loss = {loss.item():.4f}")

    dist.barrier()
    duration = time.time() - start

    if rank == 0:
        print(f"Training finished in {duration:.2f} seconds")
        save_path = os.path.join(output_dir, "toy_model.pt")
        torch.save(model.state_dict(), save_path)
        print(f"Saved model to {save_path}")

    dist.destroy_process_group()


if __name__ == "__main__":
    main()
