#!/usr/bin/env python3
"""
Controls most of the system.
"""

from typing import Optional
from tqdm import tqdm

import data
import tiles
import image


def main() -> None:
    """
    Default functionality (for Elgeis).
    """
    run(
        "http://dynmap.elgeis.com:10102/",
        "8302018",
        "dynmap.png",
        "cache",
        None,
        2,
        "flat",
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
        # Multiply width bby 6
        size = tuple([tuple(x * 6.2 for x in size[0]), size[1]])

    tilesize = tiles.get_tilesize(zoom)
    rangeX, rangeZ = tiles.blocks_to_tiles(*size[0], *size[1], tilesize)

    full_map = image.init(rangeX, rangeZ)

    pbar = tqdm(
        total=(rangeX[1] + 1 - rangeX[0]) * (rangeZ[1] + 1 - rangeZ[0])
    )

    startX = rangeX[0]
    startZ = rangeZ[0]
    for X in range(rangeX[0], rangeX[1] + 1):
        for Z in range(rangeZ[0], rangeZ[1] + 1):
            tile = data.getimage(templates, X, Z, zoom)
            image.append(full_map, tile, X - startX, Z - startZ)
            del tile
            pbar.update(1)
    pbar.close()

    full_map = image.trim(full_map, zoom, size, (rangeX, rangeZ))
    print("Saving image. This may take a while.")
    full_map.save(output)


if __name__ == "__main__":
    main()
