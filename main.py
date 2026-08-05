#!/usr/bin/env python3
"""
Controls most of the system.
"""

from typing import Optional
from tqdm import tqdm
from traceback import print_exc
from datetime import date
from shutil import rmtree
from os import path, cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

import data
import tiles
import image


def main() -> None:
    """
    Default functionality (for Elgeis).
    """
    print("Running with default parameters (Elgeis dynmap).")
    run(
        "http://dynmap.elgeis.com:10102/",
        "8302018",
        None, #"dynmap.png",
        None, #"cache",
        None,
        4,
        "flat2",
        False,
    )


def run(
    link: str,
    worldname: str,
    output: str,
    cache: Optional[str],
    size: Optional[tuple[tuple[int, int], tuple[int, int]]],
    zoom: int,
    mapname: Optional[str],
    isometic: Optional[bool]
) -> None:
    """
    The primary function that delegates to the other modules.
    """
    
    if size is None:
        size = data.worldborder(link, worldname, mapname)
    templates = data.templating(link, cache, worldname, zoom, mapname)

    if isometic:
        # Multiply height by 3
        size = tuple([size[0], tuple(x * 3.2 for x in size[1])])
        # Multiply width by 6
        size = tuple([tuple(x * 6.2 for x in size[0]), size[1]])
    
    if output is None:
        output = "dynmap_" + date.today().isoformat() + ".png"

    tilesize = tiles.get_tilesize(zoom)
    rangeX, rangeZ = tiles.blocks_to_tiles(*size[0], *size[1], tilesize)

    full_map = image.init(rangeX, rangeZ)

    pbar = tqdm(
        total=(rangeX[1] + 1 - rangeX[0]) * (rangeZ[1] + 1 - rangeZ[0])
    )

    startX = rangeX[0]
    startZ = rangeZ[0]
    # for X in range(rangeX[0], rangeX[1] + 1):
    #     for Z in range(rangeZ[0], rangeZ[1] + 1):
    #         try:
    #             tile = data.getimage(templates, X, Z, zoom)
    #             image.append(full_map, tile, X - startX, Z - startZ)
    #             tile.close()
    #             del tile
    #             pbar.update(1)
    #         except Exception:
    #             print("==========================================")
    #             print(f"\nFailed while processing tile X={X}, Z={Z}")
    #             print_exc()
    #             input("\nPress anything TWICE to close...")
    #             input("\nPress anything TWICE to close...")
    #             print("==========================================")

    with ThreadPoolExecutor(max_workers=min(32, (cpu_count() or 4) * 2)) as executor:
        futures = {
            executor.submit(data.getimage, templates, X, Z, zoom): (X, Z)
            for X in range(rangeX[0], rangeX[1] + 1)
            for Z in range(rangeZ[0], rangeZ[1] + 1)
        }

        for future in as_completed(futures):

            X, Z = futures[future]

            try:
                tile = future.result()

                image.append(full_map, tile, X - startX, Z - startZ)

                tile.close()
                pbar.update(1)

            except Exception:
                print("==========================================")
                print(f"Failed while processing tile X={X}, Z={Z}")
                print_exc()
                print("==========================================")

                # Cancel any downloads that haven't started yet
                executor.shutdown(wait=False, cancel_futures=True)

                raise

    pbar.close()

    #full_map.save("initial.png")
    full_map = image.trim(full_map, zoom, size, (rangeX, rangeZ))
    print("Saving image. This may take a while.")
    full_map.save(output)

    if cache and path.isdir(cache):
        try:
            rmtree(cache)
            print(f'Deleted cache folder "{cache}".')
        except Exception as e:
            print(f'Unable to delete cache folder "{cache}": {e}')

def load_tile(args):
    X, Z, templates, zoom = args
    tile = data.getimage(templates, X, Z, zoom)
    return X, Z, tile


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("==========================================")
        print("\nProgram cancelled by user. (ctrl+c closes terminals)")
        input("\nPress Enter TWICE to close...")
        input("\nPress Enter TWICE to close...")
        print("==========================================")
    except Exception:
        print("==========================================")
        print("\nAn unexpected error occurred.")
        print("---------------")
        print_exc()
        input("\nPress Enter TWICE to close...")
        input("\nPress Enter TWICE to close...")
        print("==========================================")
