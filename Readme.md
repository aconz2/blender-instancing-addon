Blender addon to create empties at verts, edges, and/or faces. See [demo video](https://www.youtube.com/watch?v=1XHZL3BMYok)

# Verts
Empty is placed at the vertex with its +Z along the vertex normal. Other two axes are arbitrary

# Edges
Only edges which join two faces are currently processed. A warning will be issued on how many edges are skipped.

Empty is placed at the midpoint with its +Z halfway between the face normals of its two adjacent faces. X is along the edge (sign is arbitrary). Y is arbitrary.

# Faces
Empty is placed at the median center with its +Z along the face normal. X is along one of the faces edge (which edge and its sign are arbitrary). Y is arbitrary.
