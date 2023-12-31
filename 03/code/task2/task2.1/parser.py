import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="General configuration for micromind.")

    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate.")
    parser.add_argument(
        "--optimizer",
        dest="opt",
        default="adam",
        choices=["adam", "sgd", "adamW", "adadelta", "sparseadam", "nadam"],
        help="Optimizer name.",
    )
    parser.add_argument(
        "--experiment_name", default="exp", help="Name of the experiment."
    )
    parser.add_argument(
        "--output_folder", default="results", help="Output folder path."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode to check train and validation steps.",
    )
    parser.add_argument(
        "--epochs",
        default=20,
        type=int
    )
    parser.add_argument(
        "--batch_size",
        default=64,
        type=int
    )
    parser.add_argument(
        "--model_name",
        default="model01",        
    )

    args = parser.parse_args()
    return args
