from pathlib import Path
from app.geo.mapper import GeometryMapper

def test_isro_grd_columns_and_intersection(tmp_path):
    a=tmp_path/'a.csv'; b=tmp_path/'b.csv'
    a.write_text('Longitude,Latitude,Pixel,Scan\n20,-85,0,0\n21,-85,100,0\n20,-84,0,100\n21,-84,100,100\n')
    b.write_text('Longitude,Latitude,Pixel,Scan\n20.5,-85,0,0\n21.5,-85,100,0\n20.5,-84,0,100\n21.5,-84,100,100\n')
    ga=GeometryMapper(a); gb=GeometryMapper(b)
    assert ga.ok and gb.ok
    assert ga.pixel_window_for_bbox((-84.9,20.1,-84.1,20.9),pad=0) is not None
    assert ga.intersection_bbox(gb)==(-85.0,20.5,-84.0,21.0)
