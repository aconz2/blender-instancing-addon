bl_info = {
    'name': 'Instancing++',
    'description': 'Create empties instanced to a collection on any combination of verts, edges, and faces',
    'blender': (2, 80, 0),
    'category': 'Object',
}

import bpy
import bmesh
from mathutils import Vector, Matrix
from functools import partial

# We don't include the first collection as that is where the empty gets placed, and you can't instance your own collection
# TODO: we don't want to include the destination instance
def collection_property_callback(self, context):
    return [('', '', '')] + [(coll.name_full,) * 3 for coll in bpy.data.collections[1:]]

def make_empty(instance_collection, display_size, type):
    bpy.ops.object.empty_add(type=type)
    ret = bpy.context.object
    ret.empty_display_size = 0
    if instance_collection:
        ret.instance_type = 'COLLECTION'
        ret.instance_collection = instance_collection
    ret.empty_display_size = display_size
    return ret

def change_of_basis_matrix(at, i, j, k):
    rot = Matrix([i.normalized(), j.normalized(), k.normalized()])
    return Matrix.Translation(at) @ rot.transposed().to_4x4()

def edge_normal(edge):
    faces = list(edge.link_faces)
    if len(faces) > 2:
        print('WARNING got {} faces when I was only expecting 2'.format(len(faces)))
    return (faces[0].normal + faces[1].normal) / 2

class InstancingPlusPlus(bpy.types.Operator):
    bl_idname = 'object.instancing_plus'
    bl_label = 'Instancing++'
    bl_options = {'REGISTER', 'UNDO'}

    empty_type: bpy.props.EnumProperty(
        name='Empty Type',
        items=[
            ('ARROWS', 'Arrows', 'Arrows'),
            ('SINGLE_ARROW', 'Single Arrow', 'Single Arrow'),
            ('PLAIN_AXES', 'Plain Axes', 'Plain Axes'),
        ],
    )
    display_size: bpy.props.FloatProperty(name='Empty Display Size', default=0.01, min=0.01, max=10)
    which: bpy.props.BoolVectorProperty(name='Which', size=3)
    collection: bpy.props.StringProperty(name='Instance Collection', default='')
    instance_enabled: bpy.props.BoolProperty(name='Enable Instance', default=True)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = context.active_object
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)

        instance_collection = bpy.data.collections[self.collection] if (self.instance_enabled and self.collection) else None
        # print(self.collection, instance_collection)
        dest_collection = bpy.data.collections.new('Instances')
        context.scene.collection.children.link(dest_collection)

        make_empty_ = partial(make_empty, instance_collection, self.display_size, self.empty_type)

        empties = []

        # Vertices
        if self.which[0]:
            for v in mesh.verts:
                empty = make_empty_()
                # choose arbitrary x and y axes, z points along vector normal
                k = v.normal
                i = k.orthogonal()
                j = k.cross(i)
                empty.matrix_local = change_of_basis_matrix(v.co, i, j, k)
                empties.append(empty)

        # Edge
        if self.which[1]:
            for e in mesh.edges:
                empty = make_empty_()
                # choose x along edge, z as the vector bisector of its two face normals, and cross for y
                k = edge_normal(e)
                i = e.verts[1].co - e.verts[0].co
                j = k.cross(i)
                mid = (e.verts[0].co + e.verts[1].co) / 2
                empty.matrix_local = change_of_basis_matrix(mid, i, j, k)
                empties.append(empty)

        # Faces
        if self.which[2]:
            for f in mesh.faces:
                empty = make_empty_()
                # choose x along an edge and z points along vector normal
                edge = f.edges[0]
                k = f.normal
                i = edge.verts[1].co - edge.verts[0].co
                j = k.cross(i)
                empty.matrix_local = change_of_basis_matrix(f.calc_center_median(), i, j, k)
                empties.append(empty)

        for e in empties:
            e.scale.xyz = 1, 1, 1  # TODO: figure out why the matrix transform doesn't maintain scale
            currently_in = e.users_collection
            dest_collection.objects.link(e)
            for c in currently_in:
                c.objects.unlink(e)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        title_size = 0.6

        row = col.split(factor=title_size, align=True)
        row.label(text='Empty Type')
        row.prop(self, 'empty_type', text='')

        row = col.split(factor=title_size, align=True)
        row.label(text='Instance Collection')
        # TODO: there is too much spacing between the checkbox and search box
        row.prop(self, 'instance_enabled', text='')
        row.prop_search(self, 'collection', bpy.data, 'collections', text='')

        row = layout.row()
        for i, text in enumerate(('Verts', 'Edges', 'Faces')):
            row.prop(self, 'which', index=i, text=text, toggle=True)

        layout.row().prop(self, 'display_size')

def register():
    bpy.utils.register_class(InstancingPlusPlus)

def unregister():
    bpy.utils.unregister_class(InstancingPlusPlus)

if __name__ == '__main__':
    # print('-' * 80)
    try:
        unregister()
    except Exception:
        pass
    register()
