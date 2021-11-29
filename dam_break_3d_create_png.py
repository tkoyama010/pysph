import pyvista as pv
import pyvista


pv.start_xvfb()
mesh = pv.read("./dam_break_3d_output/dam_break_3d_fluid_4205.vtu")
plotter = pv.Plotter(shape=(2, 2), lighting=None)
plotter.set_background("white")
plotter.enable_parallel_projection()
plotter.enable_eye_dome_lighting()
plotter.subplot(0, 0)
plotter.add_mesh(
    mesh,
    color="white",
    pbr=True,
    metallic=0.5,
    roughness=0.5,
    diffuse=1,
    render_points_as_spheres=True,
)

plotter.subplot(0, 1)
plotter.add_mesh(
    mesh,
    color="white",
    pbr=True,
    metallic=0.5,
    roughness=0.5,
    diffuse=1,
    render_points_as_spheres=True,
)
plotter.show(
    interactive=False, screenshot="dam_break_3d_output/dam_break_3d_fluid_4205.png"
)
