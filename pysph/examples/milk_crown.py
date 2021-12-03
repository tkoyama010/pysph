"""Three-dimensional dam break over a dry bed. (14 hours)

The case is described as a SPHERIC benchmark
https://app.spheric-sph.org/sites/spheric/files/SPHERIC_Test2_v1p1.pdf

By default the simulation runs for 6 seconds of simulation time.
"""

import numpy as np

from pysph.base.kernels import WendlandQuintic
from pysph.solver.application import Application
from pysph.sph.integrator import EPECIntegrator
from pysph.sph.scheme import WCSPHScheme
import logging
logging.basicConfig(level=logging.INFO)

import sys
sys.path.insert(0, ".")
from _db_geometry import MilkCrownGeometry

dim = 3

dt = 1.2e-5
tf = dt*800

# parameter to change the resolution
dx = 0.0001
nboundary_layers = 1
hdx = 1.3
ro = 1000.0
h0 = dx * hdx
gamma = 7.0
alpha = 0.25
beta = 0.0
c0 = 10.0 * np.sqrt(2.0 * 9.81 * 0.55)


class MilkCrown(Application):
    def add_user_options(self, group):
        group.add_argument(
            '--dx', action='store', type=float, dest='dx',  default=dx,
            help='Particle spacing.'
        )
        group.add_argument(
            '--hdx', action='store', type=float, dest='hdx',  default=hdx,
            help='Specify the hdx factor where h = hdx * dx.'
        )

    def consume_user_options(self):
        dx = self.options.dx
        self.dx = dx
        self.hdx = self.options.hdx
        self.geom = MilkCrownGeometry(
            dx=dx, nboundary_layers=nboundary_layers, hdx=self.hdx, rho0=ro,
            with_obstacle=False,
            container_height=0.0240,
            container_width=0.040,
            container_length=0.040,
            fluid_column_height=0.001,
            fluid_column_width=0.040,
            fluid_column_length=0.040,
            fluid_droplet_center_x=0.02,
            fluid_droplet_center_y=0.00,
            fluid_droplet_center_z=0.005,
            fluid_droplet_radius=0.002,
            fluid_droplet_initial_velocity_x=0.0,
            fluid_droplet_initial_velocity_y=0.0,
            fluid_droplet_initial_velocity_z=-2.8,
        )
        self.co = 10.0 * self.geom.get_max_speed(g=9.81)

    def create_scheme(self):
        s = WCSPHScheme(
            ['fluid'], ['boundary'], dim=dim, rho0=ro, c0=c0,
            h0=h0, hdx=hdx, gz=-9.81, alpha=alpha, beta=beta, gamma=gamma,
            hg_correction=True, tensile_correction=False
        )
        return s

    def configure_scheme(self):
        s = self.scheme
        hdx = self.hdx
        kernel = WendlandQuintic(dim=dim)
        h0 = self.dx * hdx
        s.configure(h0=h0, hdx=hdx)
        dt = 0.25*h0/(1.1 * self.co)
        s.configure_solver(
            kernel=kernel, integrator_cls=EPECIntegrator, tf=tf, dt=dt,
            adaptive_timestep=True, n_damp=50,
            output_at_times=np.arange(0.0, tf, dt*20)
        )

    def create_particles(self):
        return self.geom.create_particles()

    def customize_output(self):
        self._mayavi_config('''
        viewer.scalar = 'u'
        b = particle_arrays['boundary']
        b.plot.actor.mapper.scalar_visibility = False
        b.plot.actor.property.opacity = 0.1
        ''')

    def post_process(self, info_fname):
        if self.rank > 0:
            return
        import os
        if os.path.exists(info_fname):
            self.read_info(info_fname)
        else:
            return

        if len(self.output_files) == 0:
            return

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            print("Post processing requires matplotlib")
            return
        from pysph.solver.utils import iter_output
        from pysph.examples import db_exp_data as dbd
        from pysph.tools.interpolator import Interpolator
        H = self.geom.fluid_column_height
        factor_y = 1/(ro*9.81*H)
        factor_x = np.sqrt(9.81/H)

        # t1, t3, data_p1, data_p3 = dbd.get_kleefsman_data()
        files = self.output_files

        t = []
        p0 = []

        p_x = np.repeat(0, 2)
        p_y = np.repeat(0, 2)
        p_z = np.array([0.021, 0.101])

        for sd, arrays1, arrays3 in iter_output(
                files, "fluid", "boundary"
        ):
            t.append(sd["t"]*factor_x)
            interp = Interpolator([arrays1, arrays3],
                                  x=p_x, y=p_y, z=p_z, method="shepard")
            p0.append(interp.interpolate('p')*factor_y)

        fname = os.path.join(self.output_dir, 'results.npz')
        t, p0 = list(map(np.asarray, (t, p0)))
        np.savez(fname, t=t, p0=p0)

        # p1 = p0[:, 0]
        # p3 = p0[:, 1]

        # fig1 = plt.figure()
        # plt.plot(t, p1, label="p1 computed", figure=fig1)
        # plt.plot(t1, data_p1, label="Kleefsman et al.", figure=fig1)
        # plt.legend()
        # plt.ylabel(r"$\frac{P}{\rho gH}$")
        # plt.xlabel(r"$t \sqrt{\frac{g}{H}} $")
        # plt.title("P1")
        # plt.savefig(os.path.join(self.output_dir, 'p1_vs_t.png'))

        # fig2 = plt.figure()
        # plt.plot(t, p3, label="p3 computed", figure=fig2)
        # plt.plot(t3, data_p3, label="Kleefsman et al.", figure=fig2)
        # plt.legend()
        # plt.ylabel(r"$\frac{P}{\rho gH}$")
        # plt.xlabel(r"$t \sqrt{\frac{g}{H}} $")
        # plt.title("P3")
        # plt.savefig(os.path.join(self.output_dir, 'p3_vs_t.png'))


if __name__ == '__main__':
    app = MilkCrown()
    app.run()
    app.post_process(app.info_filename)
