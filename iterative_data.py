from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
import random

import pandas as pd


def iter_load_data(
	file_path: str,
	sep: str = "|",
	encoding: str = "latin1",
	chunksize: int = 50_000,
	usecols: list[str] | None = None,
	dtype: dict[str, str] | None = None,
) -> Iterator[pd.DataFrame]:
	"""
	Read a delimited file in chunks to keep memory usage bounded.

	This function yields DataFrames chunk by chunk instead of loading the
	complete dataset in memory.
	"""
	if chunksize <= 0:
		raise ValueError("chunksize must be greater than 0")

	reader = pd.read_csv(
		file_path,
		sep=sep,
		encoding=encoding,
		chunksize=chunksize,
		usecols=usecols,
		dtype=dtype,
		low_memory=True,
	)

	for chunk in reader:
		yield chunk


def process_data_iteratively(
	file_path: str,
	process_chunk: Callable[[pd.DataFrame], None],
	sep: str = "|",
	encoding: str = "latin1",
	chunksize: int = 50_000,
	usecols: list[str] | None = None,
	dtype: dict[str, str] | None = None,
) -> int:
	"""
	Apply a callback to each chunk and return total processed rows.
	"""
	total_rows = 0
	for chunk in iter_load_data(
		file_path=file_path,
		sep=sep,
		encoding=encoding,
		chunksize=chunksize,
		usecols=usecols,
		dtype=dtype,
	):
		process_chunk(chunk)
		total_rows += len(chunk)
	return total_rows


def convert_apnea_to_binary(chunk: pd.DataFrame) -> pd.DataFrame:
	"""
	Convert Apnea column to binary values.

	Transforms "No" to 0, and any other value to 1.
	"""
	if "Apnea" in chunk.columns:
		chunk["Apnea"] = chunk["Apnea"].apply(lambda x: 0 if x == "No" else 1)
	return chunk


def split_chunk_train_val_test(
	chunk: pd.DataFrame,
	train_ratio: float,
	val_ratio: float,
	seed_rng: random.Random,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""
	Split a chunk into train, validation, and test subsets.
	"""
	test_ratio = 1.0 - train_ratio - val_ratio
	if train_ratio < 0 or val_ratio < 0 or test_ratio < 0:
		raise ValueError("Split ratios must be non-negative and sum to 1 or less")

	if chunk.empty:
		return chunk, chunk, chunk

	random_values = pd.Series(
		[seed_rng.random() for _ in range(len(chunk))],
		index=chunk.index,
	)

	train_chunk = chunk[random_values < train_ratio]
	val_chunk = chunk[(random_values >= train_ratio) & (random_values < train_ratio + val_ratio)]
	test_chunk = chunk[random_values >= train_ratio + val_ratio]

	return train_chunk, val_chunk, test_chunk


def save_filtered_data_iterative(
	input_file_path: str,
	output_file_path: str,
	columns: list[str],
	sep: str = "|",
	encoding: str = "latin1",
	chunksize: int = 50_000,
) -> int:
	"""
	Save selected columns to a CSV file using chunked reads/writes.

	Returns the total number of rows written.
	"""
	output_path = Path(output_file_path)
	if output_path.exists():
		output_path.unlink()

	total_written = 0
	write_header = True

	for chunk in iter_load_data(
		file_path=input_file_path,
		sep=sep,
		encoding=encoding,
		chunksize=chunksize,
		usecols=columns,
	):
		chunk = convert_apnea_to_binary(chunk)
		chunk.to_csv(output_path, mode="a", index=False, header=write_header)
		write_header = False
		total_written += len(chunk)

	return total_written


def save_split_data_iterative(
	input_file_path: str,
	train_output_path: str,
	val_output_path: str,
	test_output_path: str,
	columns: list[str],
	sep: str = "|",
	encoding: str = "latin1",
	chunksize: int = 50_000,
	train_ratio: float = 0.7,
	val_ratio: float = 0.15,
	seed: int = 42,
) -> dict[str, int]:
	"""
	Save the dataset into train, validation, and test CSV files using chunks.

	Returns the number of rows written to each split.
	"""
	test_ratio = 1.0 - train_ratio - val_ratio
	if train_ratio < 0 or val_ratio < 0 or test_ratio < 0:
		raise ValueError("Split ratios must be non-negative and sum to 1 or less")

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
	seed_rng = random.Random(seed)

	for chunk in iter_load_data(
		file_path=input_file_path,
		sep=sep,
		encoding=encoding,
		chunksize=chunksize,
		usecols=columns,
	):
		chunk = convert_apnea_to_binary(chunk)
		train_chunk, val_chunk, test_chunk = split_chunk_train_val_test(
			chunk=chunk,
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

	return rows_written


if __name__ == "__main__":
	input_path = "CaobaApneaSueno.txt"
	selected_columns = ["EnfermedadActual", "Apnea"]

	rows = save_split_data_iterative(
		input_file_path=input_path,
		columns=selected_columns,
		chunksize=25_000,
		train_output_path="datos_apnea_train.csv",
		val_output_path="datos_apnea_val.csv",
		test_output_path="datos_apnea_test.csv",
	)
	print(f"Rows written by split: {rows}")