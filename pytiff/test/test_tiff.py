from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.extra.numpy import arrays
from pytiff import *
import hypothesis.strategies as st
import numpy as np
import pytest
import subprocess
import tifffile

TILED_GREY = "test_data/small_example_tiled.tif"
NOT_TILED_GREY = "test_data/small_example.tif"
TILED_RGB = "test_data/tiled_rgb_sample.tif"
NOT_TILED_RGB = "test_data/rgb_sample.tif"
TILED_BIG = "test_data/bigtif_example_tiled.tif"
NOT_TILED_BIG = "test_data/bigtif_example.tif"
NO_FILE = "test_data/not_here.tif"

def test_open():
    tif = Tiff(TILED_GREY)
    assert True

def test_open_fail():
    with pytest.raises(IOError):
        tif = Tiff(NO_FILE)

def test_greyscale_tiled():
    with Tiff(TILED_GREY) as tif:
        assert tif.is_tiled()
    read_methods(TILED_GREY)

def test_large_slice():
    with Tiff(TILED_GREY) as tif:
        assert tif.is_tiled()
        data = tif[:]

    with Tiff(TILED_GREY) as tif:
        shape = tif.shape
        large = tif[0:shape[0]+100, 0:shape[1]+33]

    assert np.all(data == large)

def test_greyscale_not_tiled():
    with Tiff(NOT_TILED_GREY) as tif:
        assert not tif.is_tiled()
    read_methods(NOT_TILED_GREY)

def test_rgb_tiled():
    with tifffile.TiffFile(TILED_RGB) as tif:
        for page in tif:
            first_page = page.asarray()
            break

    with Tiff(TILED_RGB) as tif:
        assert tif.is_tiled()
        data = tif[:]
        # test reading whole page
        np.testing.assert_array_equal(first_page, data)
        # test reading a chunk
        chunk = tif[100:200, :, :3]
        np.testing.assert_array_equal(first_page[100:200, :], chunk)

        chunk = tif[:, 250:350]
        np.testing.assert_array_equal(first_page[:, 250:350], chunk)

        chunk = tif[100:200, 250:350]
        np.testing.assert_array_equal(first_page[100:200, 250:350], chunk)

def test_rgb_not_tiled():
    with tifffile.TiffFile(NOT_TILED_RGB) as tif:
        for page in tif:
            first_page = page.asarray()
            break
        alpha = np.ones_like(first_page[:,:,0]) * 255
        first_page = np.dstack((first_page, alpha))

    with Tiff(NOT_TILED_RGB) as tif:
        assert not tif.is_tiled()
        data = tif[:]
        # test reading whole page
        np.testing.assert_array_equal(first_page, data)
        # test reading a chunk
        chunk = tif[100:200, :]
        np.testing.assert_array_equal(first_page[100:200, :], chunk)

        chunk = tif[:, 250:350]
        np.testing.assert_array_equal(first_page[:, 250:350], chunk)

        chunk = tif[100:200, 250:350]
        np.testing.assert_array_equal(first_page[100:200, 250:350], chunk)

def test_big_tiled():
    with Tiff(TILED_BIG) as tif:
        assert tif.is_tiled()
    read_methods(TILED_BIG)

def test_big_not_tiled():
    with Tiff(NOT_TILED_BIG) as tif:
        assert not tif.is_tiled()
    read_methods(NOT_TILED_BIG)

def test_to_array():
    import numpy as np
    with Tiff(TILED_GREY) as tif:
        data = np.array(tif)
    with Tiff(TILED_GREY) as t:
        assert np.all(data == t[:])

MULTI_PAGE = "test_data/multi_page.tif"
N_PAGES = 4
SIZE = [(500, 500), (500, 500), (400, 640),(500, 500)]
MODE = ["greyscale", "greyscale", "rgb","greyscale"]
TYPE = [np.uint8, np.uint8, np.uint8, np.uint16]

def test_multi_page():
    with Tiff(MULTI_PAGE) as tif:
        assert tif.number_of_pages == N_PAGES
        assert tif.current_page == 0
        tif.set_page(2)
        assert tif.current_page == 2
        tif.set_page(N_PAGES + 1)
        assert tif.current_page == 3
        for i in range(N_PAGES):
            tif.set_page(i)
            assert tif.size == SIZE[i]
            assert tif.mode == MODE[i]
            assert tif.dtype == TYPE[i]

def test_generator_multi_page():
    with Tiff(MULTI_PAGE) as tif:
        for i, page in enumerate(tif):
            assert page.size == SIZE[i]
            assert page.mode == MODE[i]
            assert page.dtype == TYPE[i]

def read_methods(filename):
    with tifffile.TiffFile(filename) as tif:
        for page in tif:
            first_page = page.asarray()
            break

    with Tiff(filename) as tif:
        data = tif[:]
        # test reading whole page
        np.testing.assert_array_equal(first_page, data)
        # test reading a chunk
        chunk = tif[100:200, :, :3]
        np.testing.assert_array_equal(first_page[100:200, :], chunk)

        chunk = tif[:, 250:350]
        np.testing.assert_array_equal(first_page[:, 250:350], chunk)

        chunk = tif[100:200, 250:350]
        np.testing.assert_array_equal(first_page[100:200, 250:350], chunk)

OUT_FILE = "test_data/tmp.tif"
MAX_SAMPLES = 100
MAX_ITER = 1000

def random(shape,dtype):
    ints = [np.int8, np.int16, np.int32,np.int64, np.uint8, np.uint16, np.uint32,np.uint64]
    if dtype in [np.int8, np.int16, np.int32,np.int64]:
        return np.random.randint(low=np.iinfo(dtype).min, high=np.iinfo(dtype).max, size=shape).astype(dtype)
    else:
        return np.random.rand(shape[0], shape[1]).astype(dtype)


@st.composite
def random_matrix(draw, dtype=np.int8, min_row=0, max_row=5, min_col=0, max_col=5):
    rows = draw(st.integers(min_value=min_row,max_value=max_row))
    cols =draw(st.integers(min_value=min_col, max_value=max_col))
    return random((rows, cols), dtype)


# scanline integer tests

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int8_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int16, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int16_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int32, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int32_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int64, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int64_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

# tile integer tests

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int8_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int16, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int16_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int32, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int32_tile(data):
    print(data.shape)
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int64, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_int64_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

# unsigned int tests

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_uint8_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.uint16, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_uint16_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.uint32, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_uint32_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.uint64, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_uint64_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

# float tests

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.float16, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_float16_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.float32, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_float32_scanline(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="scanline")

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.float64, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_float64_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data=random_matrix(dtype=np.int8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_append_int8_tile(data):
    with Tiff(OUT_FILE, "w") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with Tiff(OUT_FILE, "a") as handle:
        handle.write(data, method="tile", tile_width=16, tile_length=16)

    with Tiff(OUT_FILE, "r") as handle:
        assert handle.number_of_pages == 2

    with tifffile.TiffFile(OUT_FILE) as handle:
        img = handle.asarray()
        assert data.dtype == img.dtype
        assert np.all(data == img)

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data1=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data2=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data3=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data4=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_chunk(data1, data2, data3, data4):
    with Tiff(OUT_FILE, "w")as handle:
        chunks = [data1, data2, data3, data4]
        handle.new_page((2000, 2000), dtype=np.uint8, tile_length=16, tile_width=16)
        row = 0
        col = 0
        max_row_end = 0
        positions = []
        for c in chunks:
            shape = c.shape
            row_end, col_end = row + shape[0], col + shape[1]
            max_row_end = max(max_row_end, row_end)
            handle[row:row_end, col:col_end] = c
            # save for reading chunks
            positions.append([row, row_end, col, col_end])
            if col_end >= handle.shape[1]:
                col = 0
                row = max_row_end
            else:
                col = col_end

        handle.save_page()

    with Tiff(OUT_FILE) as handle:
        for pos, chunk in zip(positions, chunks):
            row, row_end, col, col_end = pos
            data = handle[row:row_end, col:col_end]
            assert np.all(data == chunk)

    with Tiff(OUT_FILE) as handle:
        with pytest.raises(ValueError):
            handle.new_page((50, 50), np.dtype("uint8"))
            handle[:, :] = np.random.rand(50, 50)
            handle.save_page()

    subprocess.call(["rm", OUT_FILE])

@settings(max_examples=MAX_SAMPLES, max_iterations=MAX_ITER)
@given(data1=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data2=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data3=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500),
       data4=random_matrix(dtype=np.uint8, min_row=100, max_row=500, min_col=100, max_col=500))
def test_write_chunk_multiple_pages(data1, data2, data3, data4):
    with Tiff(OUT_FILE, "w")as handle:
        chunks = [data1, data2, data3, data4]

        for c in chunks:
            shape = c.shape
            handle.new_page(shape, dtype=np.uint8, tile_length=16, tile_width=16)
            handle[:] = c

    with Tiff(OUT_FILE) as handle:
        for page, chunk in enumerate(chunks):
            handle.set_page(page)
            data = handle[:]
            assert data.shape == chunk.shape
            assert np.all(data == chunk)

    subprocess.call(["rm", OUT_FILE])
