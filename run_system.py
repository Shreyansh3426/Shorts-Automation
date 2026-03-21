import subprocess
import time

VIDEOS_PER_RUN = 3  # start safe


def run(cmd):
    print(f"\n🚀 Running: {cmd}\n")
    subprocess.run(cmd, shell=True)


def main():
    print("🔥 SYSTEM STARTED\n")

    # 1. mine trends
    run("python trend_miner.py")

    for i in range(VIDEOS_PER_RUN):
        print(f"\n🎬 GENERATING VIDEO {i+1}\n")

        # 2. generate + pipeline (this already chains everything)
        run("python auto_pipeline.py")

        # small delay to avoid API spam
        time.sleep(5)

    print("\n✅ RUN COMPLETE\n")


if __name__ == "__main__":
    main()
