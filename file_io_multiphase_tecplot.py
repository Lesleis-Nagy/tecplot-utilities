import linecache
import numpy as np
import re

from collections import OrderedDict

regex_title = re.compile(r"TITLE\s*=\s*\"(.*)\"")
regex_variables = re.compile(r"VARIABLES\s*=\s*(\"[a-zA-Z]+\"(\s*,\s*\"[a-zA-Z]+\")*)")
regex_zone = re.compile(r"ZONE T\s*=\s*\"([a-zA-Z0-9\.\s_\-\+]*)\"")
regex_nvert = re.compile(r"N\s*=\s*([0-9]+)")
regex_nelem = re.compile(r"E\s*=\s*([0-9]+)")
regex_f = re.compile(r"F\s*=\s*(POINT|BLOCK|FEPOINT|FEBLOCK)")
regex_et = re.compile(r"ET\s*=\s*(TRIANGLE|BRICK|QUADRILATERAL|TETRAHEDRON)")
regex_varlocation = re.compile(r"VARLOCATION\s*=\s*\(([A-Z0-9-,\[\]=]+)\)")
regex_varsharelist = re.compile(r"VARSHARELIST\s*=\s*\(([0-9-,\[\]=]+)\)")
regex_connectivitysharezone = re.compile(r"CONNECTIVITYSHAREZONE\s*=\s*([0-9]+)")
regex_floats = re.compile("(-?[0-9]+\.[0-9]+E[+-]?[0-9]{2}(\s+-?[0-9]+\.[0-9]+E[+-]?[0-9]{2})*)")


class HeaderData:
    def __init__(self):
        self.title = None
        self.variables = None

    def __str__(self):
        return "Header data\n" \
               "\ttitle:     '{}'\n" \
               "\tvariables: '{}'\n".format(self.title, self.variables)


def parse_header(tecplot_file):
    r"""
    Parse header information form a tecplot file
    :param tecplot_file: the path to the tecplot file
    :return: tuple: (line_number, title, variables, zone, no. of vertices, no. of elements, point type, element type)
    """
    current_line_no = 1
    header_data = HeaderData()
    while linecache.getline(tecplot_file, current_line_no) != '':
        line = linecache.getline(tecplot_file, current_line_no)
        match_floats = regex_floats.search(line)
        if match_floats:
            # We've hit a data section, and so are no longer parsing header information
            break
        match_title = regex_title.search(line)
        if match_title:
            header_data.title = match_title.group(1).strip()
        match_variables = regex_variables.search(line)
        if match_variables:
            header_data.variables = [val.replace("\"", "").strip() for val in match_variables.group(1).split(",")]
        current_line_no += 1
    return header_data


class ZoneData:
    def __init__(self):
        self.t = None
        self.n = None
        self.e = None
        self.f = None
        self.et = None
        self.varsharelist = None
        self.connectivitysharezone = None
        self.varlocation = None
        self.line_no = None
        self.is_first = None

    def __str__(self):
        return "Zone data\n" \
               "\tis_first:              {}\n" \
               "\tt:                     {}\n" \
               "\tn:                     {}\n" \
               "\te:                     {}\n" \
               "\tf:                     {}\n" \
               "\tet:                    {}\n" \
               "\tvarsharelist:          {}\n" \
               "\tconnectivitysharezone: {}\n" \
               "\tvarlocation:           {}\n" \
               "\tline_no:               {}\n".format(self.is_first, self.t, self.n, self.e, self.f, self.et,
                                                      self.varsharelist, self.connectivitysharezone, self.varlocation,
                                                      self.line_no)


def parse_zone_metadata(tecplot_file):
    r"""
    Find the start point of all data for each zone.
    :param tecplot_file:
    :return:
    """
    zones_data = []
    current_zone = None
    current_line_no = 1
    while linecache.getline(tecplot_file, current_line_no) != '':
        line = linecache.getline(tecplot_file, current_line_no)
        match_zone = regex_zone.search(line)
        if match_zone:
            current_zone = ZoneData()
            current_zone.t = match_zone.group(1).strip()
        match_nvert = regex_nvert.search(line)
        if match_nvert:
            current_zone.n = int(match_nvert.group(1))
        match_nelem = regex_nelem.search(line)
        if match_nelem:
            current_zone.e = int(match_nelem.group(1))
        match_f = regex_f.search(line)
        if match_f:
            current_zone.f = match_f.group(1).strip()
        match_et = regex_et.search(line)
        if match_et:
            current_zone.et = match_et.group(1).strip()
        match_varsharelist = regex_varsharelist.search(line)
        if match_varsharelist:
            current_zone.varsharelist = match_varsharelist.group(1).strip()
        match_connectivitysharezone = regex_connectivitysharezone.search(line)
        if match_connectivitysharezone:
            current_zone.connectivitysharezone = match_connectivitysharezone.group(1).strip()
        match_varlocation = regex_varlocation.search(line)
        if match_varlocation:
            current_zone.varlocation = match_varlocation.group(1).strip()
        match_floats = regex_floats.search(line)
        if match_floats:
            if current_zone is not None:
                if len(zones_data) == 0:
                    current_zone.is_first = True
                else:
                    current_zone.is_first = False
                current_zone.line_no = current_line_no
                zones_data.append(current_zone)
                current_zone = None
        current_line_no += 1
    return zones_data


def parse_zone(tecplot_file, zone_metadata, index_offset=-1):
    # Parse vertex data
    if not zone_metadata.is_first:
        vertex_data = OrderedDict([
            ('mx', []),
            ('my', []),
            ('mz', [])
        ])
    else:
        vertex_data = OrderedDict([
            ('x', []),
            ('y', []),
            ('z', []),
            ('mx', []),
            ('my', []),
            ('mz', [])
        ])
    current_line_no = zone_metadata.line_no
    nvert = zone_metadata.n
    nelem = zone_metadata.e
    for key, data in vertex_data.items():
        while len(data) < nvert and linecache.getline(tecplot_file, current_line_no) != '':
            line = linecache.getline(tecplot_file, current_line_no)
            data.extend([float(val.strip()) for val in re.split(r"\s+", line.strip())])
            current_line_no += 1
    if not zone_metadata.is_first:
        # If this is not the first zone, return magnetization data only
        return (
            None,
            list(zip(vertex_data['mx'], vertex_data['my'], vertex_data['mz'])),
            None,
            None
        )
    # Parse element data
    submesh_idxs = []
    while len(submesh_idxs) < nelem and linecache.getline(tecplot_file, current_line_no) != '':
        line = linecache.getline(tecplot_file, current_line_no)
        submesh_idxs.extend([int(val.strip()) for val in re.split(r"\s+", line.strip())])
        current_line_no += 1
    element_idxs = []
    while len(element_idxs) < nelem and linecache.getline(tecplot_file, current_line_no) != '':
        line = linecache.getline(tecplot_file, current_line_no)
        element_idxs.append(tuple([int(val.strip()) + index_offset for val in re.split(r"\s+", line.strip())]))
        current_line_no += 1
    # Return data for the first zone
    return (
        list(zip(vertex_data['x'], vertex_data['y'], vertex_data['z'])),
        list(zip(vertex_data['mx'], vertex_data['my'], vertex_data['mz'])),
        submesh_idxs,
        element_idxs
    )


def read_tecplot(tecplot_file):
    header_data = parse_header(tecplot_file)
    zones_metadata = parse_zone_metadata(tecplot_file)
    fields = []
    vertices = None
    elements = None
    submesh_idxs = None
    for zone_metadata in zones_metadata:
        v, f, sidxs, eidxs = parse_zone(tecplot_file, zone_metadata)
        if zone_metadata.is_first:
            fields.append(np.array(f, dtype=np.float64))
            vertices = np.array(v, dtype=np.float64)
            elements = np.array(eidxs, dtype=np.uint64)
            submesh_idxs = np.array(sidxs, dtype=np.uint64)
        else:
            fields.append(np.array(f, dtype=np.float64))
    return {
        "fields": fields,
        "vertices": vertices,
        "elements": elements,
        "submesh_idxs": submesh_idxs,
        "nvert": len(vertices),
        "nelem": len(elements),
        "nfields": len(fields)
    }


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def frmt_float(f):
    if f < 0:
        return "{:0.7E}".format(f)
    else:
        return " {:0.7E}".format(f)


def write_tecplot(tecplot_file, header_data, data, field_idx=None):
    write_all_fields = False
    if field_idx is None:
        write_all_fields = True
        field_idx = 0
    with open(tecplot_file, 'w') as fout:
        # write title
        fout.write("TITLE = \"{}\"\n".format(header_data.title))
        # write variables
        variables = ",".join(['"{}"'.format(v) for v in header_data.variables])
        fout.write("VARIABLES = {}\n".format(variables))
        # Write first zone
        fout.write("ZONE T=\"1\" N={}, E={}\n".format(data['nvert'], data['nelem']))
        fout.write("F=FEBLOCK, ET=TETRAHEDRON, VARLOCATION=([7]=CELLCENTERED)\n")
        for xchunk in chunker(data['vertices'], 10):
            fout.write(" ".join([frmt_float(v[0]) for v in xchunk]) + "\n")
        for ychunk in chunker(data['vertices'], 10):
            fout.write(" ".join([frmt_float(v[1]) for v in ychunk]) + "\n")
        for zchunk in chunker(data['vertices'], 10):
            fout.write(" ".join([frmt_float(v[2]) for v in zchunk]) + "\n")
        for fxchunk in chunker(data['fields'][field_idx], 10):
            fout.write(" ".join([frmt_float(v[0]) for v in fxchunk]) + "\n")
        for fychunk in chunker(data['fields'][field_idx], 10):
            fout.write(" ".join([frmt_float(v[1]) for v in fychunk]) + "\n")
        for fzchunk in chunker(data['fields'][field_idx], 10):
            fout.write(" ".join([frmt_float(v[2]) for v in fzchunk]) + "\n")
        for subchunk in chunker(data['submesh_idxs'], 10):
            fout.write(" ".join(["{:7d}".format(v) for v in subchunk]) + "\n")
        for elem in data['elements']:
            fout.write("{:7d} {:7d} {:7d} {:7d}\n".format(
                int(elem[0]+1), int(elem[1]+1), int(elem[2]+1), int(elem[3]+1))
            )
        if data["nfields"] > 1 and write_all_fields:
            # Write subsequent fields
            for field_idx in range(1, data["nfields"]):
                fout.write("ZONE T=\"{}\" N={}, E={}\n".format(field_idx+1, data["nvert"], data["nelem"]))
                fout.write(" F=FEBLOCK, ET=TETRAHEDRON, VARSHARELIST =([1-3,7]=1),  CONNECTIVITYSHAREZONE = 1, VARLOCATION=([7]=CELLCENTERED)\n")
                for fxchunk in chunker(data['fields'][field_idx], 10):
                    fout.write(" ".join([frmt_float(v[0]) for v in fxchunk]) + "\n")
                for fychunk in chunker(data['fields'][field_idx], 10):
                    fout.write(" ".join([frmt_float(v[1]) for v in fychunk]) + "\n")
                for fzchunk in chunker(data['fields'][field_idx], 10):
                    fout.write(" ".join([frmt_float(v[2]) for v in fzchunk]) + "\n")

#
# Simple test routine for this library
#
if __name__ == '__main__':
    data = read_tecplot(
        r"C:\Users\lesle\VirtualBoxShared\fs_lnagy2\neb\03\55\18\e0\c1\d8\43\97\ac\ed\a7\11\38\bf\99\50\neb.tec"
    )
    header_data = HeaderData()
    header_data.title = "output_test_neb.tec"
    header_data.variables = ['X', 'Y', 'Z', 'Mx', 'My', 'Mz', 'SD']
    write_tecplot(r"C:\Users\lesle\VirtualBoxShared\output_test_neb.tec", header_data, data, field_idx=99)

