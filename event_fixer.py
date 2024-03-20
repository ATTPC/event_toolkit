import click
import h5py as h5
from pathlib import Path
from tqdm import trange


def make_run_path(directory: Path, run: int) -> Path:
    """Create an ATTPC run file path

    Parameters
    ----------
    directory: Path
        The Path to the directory containing run data
    run: int
        The run number

    Returns
    -------
    Path
        The Path to a run
    """
    return directory / f"run_{run:04d}.h5"


def fix_get_event_numbers(data: h5.Group, event_min: int, event_max: int) -> None:
    for idx, event in enumerate(trange(event_min, event_max, miniters=100)):
        old_key = f"evt{event}_data"
        new_key = f"evt{idx}_data"
        data.move(old_key, new_key)


def fix_event_numbers(path: Path) -> None:
    """Fix the event numbers in place on the HDF5 file

    This will ensure that the FRIBDAQ and GET event numbers of the merged
    HDF5 file are as expected (running from 0-max). The HDF5 file is modified in place.
    This is not a reversible operation so use with caution!

    Parameters
    ----------
    path: Path
        Path to the HDF5 file to be fixed.

    """
    print(f"Fixing run {path}...")
    file = h5.File(path, "r+")

    # Use the meta data to extract the event range
    meta_group = file["meta"]
    meta_data = meta_group["meta"]  # type: ignore
    event_min = int(meta_data[0])  # type: ignore
    event_max = int(meta_data[2])  # type: ignore
    event_range = event_max - event_min  # inclusive on the max as well as min

    print(f"Checking GET data...")
    # Fix data where MuTaNT event number was not reset (starts not at 0)
    if event_min != 0:
        print(f"GET MuTaNT offset detected. Fixing...")
        data = file["get"]
        for idx, event in enumerate(trange(event_min, event_max + 1, miniters=100)):
            old_key = f"evt{event}_data"
            new_key = f"evt{idx}_data"
            data.move(old_key, new_key)  # type: ignore
            old_key = f"evt{event}_header"
            new_key = f"evt{idx}_header"
            data.move(old_key, new_key)  # type: ignore
        meta_data[0] = 0  # type: ignore
        meta_data[2] = event_max - event_min  # type: ignore
        print(f"GET data repaired.")

    print(f"Checking FRIB data...")
    # Get the FRIB group
    data = None
    try:
        data = file["frib"]["evt"]  # type: ignore
    except:
        print(f"Run {path} did not contain FRIBDAQ data. Skipping.")
        return

    # Make sure there's data in there
    if len(data.keys()) == 0:  # type: ignore
        print(f"Run {path} did not contain FRIBDAQ data. Skipping.")
        return

    # Check if we need fixing. If event 0 exists and event end exists, this file is ok.
    try:
        data["evt0_1903"]  # type: ignore
        print(f"Run {path} evt start looks ok. Checking end...")
        data[f"evt{event_range}_1903"]  # type: ignore
        print(f"Run {path} evt end looks ok. Skipping.")
        return
    except:
        pass

    print(f"FRIB offset detected. Fixing FRIB data...")
    # Use tqdm to display progress on this file
    for event in trange(0, event_range + 1, miniters=100):
        # This operation is only ok because we are moving keys
        # *back* one event number i.e. 1 -> 0, 2 -> 1, etc.
        # If we had to go the other direction this wouldn't work
        old_key = f"evt{event+1}_1903"
        new_key = f"evt{event}_1903"
        data.move(old_key, new_key)  # type: ignore
        old_key = f"evt{event+1}_header"
        new_key = f"evt{event}_header"
        data.move(old_key, new_key)  # type: ignore

    print(f"Run {path} fixed.")


def check_timestamps(path: Path) -> None:
    """Check that the timestamps lineup between the two event types

    Note that this can fail in cases where CoBo 10 was not instructed
    to record the timestamp of the other acquisition

    Paramters
    ---------
    path: Path
        Path to the HDF5 file to be examined.

    """

    print(f"Checking that timestamps match up between the two DAQs...")
    file = h5.File(path, "r")
    meta_group = file["meta"]
    meta_data = meta_group["meta"]  # type: ignore
    event_min = int(meta_data[0])  # type: ignore
    event_max = int(meta_data[2])  # type: ignore
    get_group = file["get"]
    frib_group = file["frib"]["evt"]  # type: ignore
    offset = float(get_group[f"evt{event_min}_header"][2]) - float(  # type: ignore
        frib_group[f"evt{event_min}_header"][1]  # type: ignore
    )
    for event in trange(event_min, event_max, miniters=100):
        get_header = get_group[f"evt{event}_header"]  # type: ignore
        frib_header = frib_group[f"evt{event}_header"]  # type: ignore
        this_offset = int(get_header[2]) - int(frib_header[1])  # type: ignore
        if this_offset - offset > 1:  # least significant bit wiggles sometimes
            print(
                f"Event {event} timestamp mismatch. Found offset of {this_offset} from get {get_header[2]} and frib {float(frib_header[1])}, expected {offset}"  # type: ignore
            )
            return
    print("Finished, timestamps match as expected")


@click.command()
@click.argument("directory", type=click.Path(exists=True))
@click.argument("run_min", type=click.INT)
@click.argument("run_max", type=click.INT)
def main(directory: str, run_min: int, run_max: int):
    """Fix the event numbers of FRIBDAQ data

    \b
    DIRECTORY is the directory containing data to be fixed
    RUN_MIN is the run number lower bound (inclusive)
    RUN_MAX is the run number upper bound (inclusive)
    """
    print("Running event number repair tool...")
    dir_path = Path(directory)
    print(f"Data Directory: {directory}")
    print(f"First run: {run_min}")
    print(f"Last run: {run_max}")
    for run in range(run_min, run_max + 1):
        path = make_run_path(dir_path, run)
        if not path.exists():
            continue
        fix_event_numbers(path)
        check_timestamps(path)


if __name__ == "__main__":
    main()
