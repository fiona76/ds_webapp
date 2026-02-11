"""Geometry engine — STEP file import, object extraction, and tessellation."""

import os

from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_TangentialDeflection


def _get_label_name(label):
    """Extract the name string from a TDF label."""
    name_attr = TDataStd_Name()
    if label.FindAttribute(TDataStd_Name.GetID_s(), name_attr):
        return name_attr.Get().ToExtString()
    return None


def _collect_solids(shape_tool, label, parent_name="", parent_location=None):
    """Recursively walk the XCAF tree and collect simple shapes (solids) with names.

    Accumulates placement transforms from component references so that each
    solid's shape is positioned correctly in the assembly coordinate system.
    """
    name = _get_label_name(label) or parent_name or "(unnamed)"
    solids = []

    if shape_tool.IsSimpleShape_s(label):
        solids.append({"name": name, "label": label, "location": parent_location})
    else:
        children = TDF_LabelSequence()
        shape_tool.GetComponents_s(label, children)
        for i in range(children.Length()):
            child = children.Value(i + 1)
            # The component label carries the placement transform
            child_loc = shape_tool.GetLocation_s(child)
            # Accumulate: parent_location * child_location
            if parent_location is not None and not parent_location.IsIdentity():
                accumulated = parent_location.Multiplied(child_loc)
            else:
                accumulated = child_loc

            ref = TDF_Label()
            if shape_tool.GetReferredShape_s(child, ref):
                solids.extend(_collect_solids(shape_tool, ref, name, accumulated))
            else:
                solids.extend(_collect_solids(shape_tool, child, name, accumulated))

    return solids


def _tessellate_shape(shape, assembly_location=None, linear_deflection=0.1):
    """Tessellate a TopoDS_Shape and return (vertices, triangles).

    Args:
        shape: the TopoDS_Shape to tessellate
        assembly_location: optional TopLoc_Location from the assembly hierarchy
        linear_deflection: mesh resolution

    Returns:
        vertices: list of (x, y, z) tuples
        triangles: list of (i0, i1, i2) index tuples
    """
    BRepMesh_IncrementalMesh(shape, linear_deflection)

    # Pre-compute assembly transform if provided
    assembly_trsf = None
    if assembly_location is not None and not assembly_location.IsIdentity():
        assembly_trsf = assembly_location.Transformation()

    vertices = []
    triangles = []
    vertex_offset = 0

    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)

        if triangulation is not None:
            face_trsf = location.Transformation()
            nb_nodes = triangulation.NbNodes()
            nb_tris = triangulation.NbTriangles()

            for i in range(1, nb_nodes + 1):
                pnt = triangulation.Node(i)
                # Apply face-level transform first (local placement)
                pnt.Transform(face_trsf)
                # Then apply assembly-level transform (global placement)
                if assembly_trsf is not None:
                    pnt.Transform(assembly_trsf)
                vertices.append((pnt.X(), pnt.Y(), pnt.Z()))

            for i in range(1, nb_tris + 1):
                tri = triangulation.Triangle(i)
                i1, i2, i3 = tri.Get()
                triangles.append((
                    i1 - 1 + vertex_offset,
                    i2 - 1 + vertex_offset,
                    i3 - 1 + vertex_offset,
                ))

            vertex_offset += nb_nodes

        explorer.Next()

    return vertices, triangles


def _extract_edges(shape, assembly_location=None, linear_deflection=0.1):
    """Extract BRep edge curves as polylines from a TopoDS_Shape.

    Args:
        shape: the TopoDS_Shape to extract edges from
        assembly_location: optional TopLoc_Location from the assembly hierarchy
        linear_deflection: curve discretization tolerance

    Returns:
        list of polylines, each a list of (x, y, z) tuples
    """
    assembly_trsf = None
    if assembly_location is not None and not assembly_location.IsIdentity():
        assembly_trsf = assembly_location.Transformation()

    edges = []
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        try:
            adaptor = BRepAdaptor_Curve(edge)
        except Exception:
            explorer.Next()
            continue

        try:
            discretizer = GCPnts_TangentialDeflection(
                adaptor, 0.05, linear_deflection
            )
        except Exception:
            explorer.Next()
            continue

        nb_points = discretizer.NbPoints()
        if nb_points < 2:
            explorer.Next()
            continue

        polyline = []
        for i in range(1, nb_points + 1):
            pnt = discretizer.Value(i)
            if assembly_trsf is not None:
                pnt.Transform(assembly_trsf)
            polyline.append((pnt.X(), pnt.Y(), pnt.Z()))
        edges.append(polyline)

        explorer.Next()

    return edges


def parse_step_file(file_path):
    """Parse a STEP file using XCAF and return solid objects with mesh data.

    Returns:
        list of dicts, each with:
            - name: object name from the STEP file
            - vertices: list of (x, y, z) tuples
            - triangles: list of (i0, i1, i2) index tuples
    """
    doc = TDocStd_Document(TCollection_ExtendedString("STEP"))
    reader = STEPCAFControl_Reader()
    status = reader.ReadFile(file_path)
    if not status:
        raise RuntimeError(f"Failed to read STEP file: {file_path}")
    reader.Transfer(doc)

    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    free_labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(free_labels)

    objects = []
    for i in range(free_labels.Length()):
        for solid_info in _collect_solids(shape_tool, free_labels.Value(i + 1)):
            shape = shape_tool.GetShape_s(solid_info["label"])
            location = solid_info.get("location")
            vertices, triangles = _tessellate_shape(shape, location)
            edge_polylines = _extract_edges(shape, location)
            if vertices and triangles:
                objects.append({
                    "name": solid_info["name"],
                    "vertices": vertices,
                    "triangles": triangles,
                    "edges": edge_polylines,
                })

    return objects


def import_step_file(file_path):
    """Import a STEP file and return metadata with mesh data.

    Returns:
        dict with keys:
            - file_path: absolute path to the STEP file
            - file_name: basename of the file
            - objects: list of dicts with name, vertices, triangles
    """
    abs_path = os.path.abspath(file_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"STEP file not found: {abs_path}")

    objects = parse_step_file(abs_path)
    return {
        "file_path": abs_path,
        "file_name": os.path.basename(abs_path),
        "objects": objects,
    }
