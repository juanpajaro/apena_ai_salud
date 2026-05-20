from __future__ import annotations

import argparse
from pathlib import Path
import random

from iterative_data import (
	convert_apnea_to_binary,
	iter_load_data,
	split_chunk_train_val_test,
)


def create_small_train_val_test_split(
	total_rows: int,
	input_file_path: str = "CaobaApneaSueno.txt",
	train_output_path: str = "datos_apnea_small_train.csv",
	val_output_path: str = "datos_apnea_small_val.csv",
	test_output_path: str = "datos_apnea_small_test.csv",
	columns: list[str] | None = None,
	train_ratio: float = 0.7,
	val_ratio: float = 0.15,
	sep: str = "|",
	encoding: str = "latin1",
	chunksize: int = 25_000,
	seed: int = 42,
) -> dict[str, int]:
	"""
	Load `CaobaApneaSueno.txt`, keep a small user-selected subset, and split it.

	`total_rows` must be between 50,000 and 100,000 (inclusive).
	Returns the number of rows written to each split file.
	"""
	if total_rows < 50_000 or total_rows > 100_000:
		raise ValueError("total_rows must be between 50,000 and 100,000")

	test_ratio = 1.0 - train_ratio - val_ratio
	if train_ratio < 0 or val_ratio < 0 or test_ratio < 0:
		raise ValueError("Split ratios must be non-negative and sum to 1 or less")

	if columns is None:
		columns = ["EnfermedadActual", "Apnea"]

	output_paths = {
		"train": Path(train_output_path),
		"val": Path(val_output_path),
		"test": Path(test_output_path),
	}
	for output_path in output_paths.values():
		if output_path.exists():
			output_path.unlink()

	write_headers = {split_name: True for split_name in output_paths}
	rows_written = {split_name: 0 for split_name in output_paths}
	total_selected = 0
	seed_rng = random.Random(seed)

	for chunk in iter_load_data(
		file_path=input_file_path,
		sep=sep,
		encoding=encoding,
		chunksize=chunksize,
		usecols=columns,
	):
		if total_selected >= total_rows:
			break

		rows_remaining = total_rows - total_selected
		small_chunk = chunk.head(rows_remaining)
		if small_chunk.empty:
			continue

		small_chunk = convert_apnea_to_binary(small_chunk)
		train_chunk, val_chunk, test_chunk = split_chunk_train_val_test(
			chunk=small_chunk,
			train_ratio=train_ratio,
			val_ratio=val_ratio,
			seed_rng=seed_rng,
		)

		for split_name, split_chunk in (
			("train", train_chunk),
			("val", val_chunk),
			("test", test_chunk),
		):
			if split_chunk.empty:
				continue
			split_chunk.to_csv(
				output_paths[split_name],
				mode="a",
				index=False,
				header=write_headers[split_name],
			)
			write_headers[split_name] = False
			rows_written[split_name] += len(split_chunk)

		total_selected += len(small_chunk)

	return rows_written


def main() -> None:
	"""Run small train/val/test split generation from the command line."""
	parser = argparse.ArgumentParser(
		description="Create a small train/val/test split from CaobaApneaSueno.txt",
	)
	parser.add_argument(
		"total_rows",
		type=int,
		help="Total rows to use, must be between 50000 and 100000",
	)
	parser.add_argument("--input", default="CaobaApneaSueno.txt", help="Input file path")
	parser.add_argument(
		"--train-output",
		default="datos_apnea_small_train.csv",
		help="Train output CSV path",
	)
	parser.add_argument(
		"--val-output",
		default="datos_apnea_small_val.csv",
		help="Validation output CSV path",
	)
	parser.add_argument(
		"--test-output",
		default="datos_apnea_small_test.csv",
		help="Test output CSV path",
	)
	parser.add_argument("--chunksize", type=int, default=25_000, help="Chunk size")
	parser.add_argument("--seed", type=int, default=42, help="Random seed")

	args = parser.parse_args()
	rows = create_small_train_val_test_split(
		total_rows=args.total_rows,
		input_file_path=args.input,
		train_output_path=args.train_output,
		val_output_path=args.val_output,
		test_output_path=args.test_output,
		chunksize=args.chunksize,
		seed=args.seed,
	)
	print(f"Rows written by split: {rows}")


if __name__ == "__main__":
	main()
