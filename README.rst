=========================================
ARIEL Follow-Up Workhouse
=========================================

This is the package that manages the execution of the ARIEL Ephemeris Refinement
from the Ground effort. It has two modes, Scheduler and Simulator.
Both are called by run.py.

- The Scheduler takes the target list and any available data and produces a list of visible transits in a given time frame for each telescope provided.
- The Simulator takes the same data and simulates the observation of the targets, generating new data as it does so, from now until a date beyond the ARIEL launch, in 2030.

Dependencies

- julian: >= 0.14
- NumPy: >= 1.160
- PyAstronomy: >= 0.13.0
- requests: >= 2.11.0


#########
Inputs
#########

General Inputs:

- Mode (-mode): Either "schedule" or "simulate", controls which mode the package will run
- Telescope Network (-te): Name of a .csv file in /telescopes/ that contains the telescope locations to be used
- Accuracy Threshold (-th): Threshold used to determine whether a target requires observation, in minutes. Can be int or float.
- Start Date (-st): Optional: Date to start from, format "YYYY-mm-dd"
- End Date (-ed): Optional: Date to end on, format "YYYY-mm-dd"

Scheduler Inputs:

- Window Length (-wl): Optional: Length of time to schedule transits for, integer

Simulator Inputs:

- Repeats (-rp): Optional: Number of runs for each simulation, defaults to 1

##########
Scheduler
##########

Forecasts the required visible transits for real targets at the telescopes provided.
When initialising:

- Providing Start Date and End Date will run between the two dates, irrespective of whether they are in the past
- Providing a Start Date and Window Length will run from the Start Date for the duration of the window
- Providing only a Window Length will run from today for the duration of the window
- Providing only an End Date will run from today until the end date
- Specifying all 3 of Start Date, End Date, and Window Length will throw an error, as will providing only a Start Date, or a setup that ends in the past, except for when using Start and End Date.

The visible transits are written to .csv files for each telescope with the name of the telescope in .csv format,
and to a file called "all_transits.csv", which contains all the transits, which are tagged with telescope name here.
These files are located in /scheduling_data/, and are currently overwritten on each run of the scheduler.

Steps:

1. Deletes existing output files and creates new ones

2. Runs the expiry calculation on all real targets with transit depths above the limit, and compiles a list of expired targets

3. For each target, forecasts transits in the specified time window and checks their visibility at each telescope provided

4. Writes list of visible transits to files

############
Simulator
############

Simulates the observation of required ARIEL targets to constrain the ephemeris timing errors from 2019 to 2030.
The dates it runs between are fixed to 12/6/2019 and 12/6/2030.

Each set of inputs given creates a new directory where the resulting data is written, and each run of the simulator creates it own directory here.
The overall results are written to a file called "results.csv" within the top-level directory, and the scheduled observations for each run of the simulation are
written inside each respective directory. They are both written to a file called "all_telescopes.csv" which contains all of them,
and individual files for each telescope.

Steps:

1. Load simulation settings and makes new directory, after deleting existing one if needed.

2. Determines the targets that need observing, and forecasts transits visible from the telescope available.

3. Schedules observations for each telescope and "observes" them, generating new data in the process.

4. Refines period data based on the new data.

5. Loops for each time window of a week.

6. Loops for the number of runs required.

##############
Depth Handling
##############

The minimum observable transit depth for a telescope depends on the telescope aperture,
the transit duration, and the stellar magnitude. For each combination of target and telescope
we calculate the minimum observable depth by approximating the relationship
between depth and stellar magnitude for a given transit duration and telescope aperture
as an exponential function of the form,

.. math::

    \Delta_{min} = Ae^{b m _{\star}}

where :math:`\Delta_{min}` is the transit depth, :math:`m_{\star}` is the stellar magnitude
and :math:`A` and :math:`b` are coefficients, which are fitted for each combination of aperture and duration.

We have fitted for the coefficients for a grid of possible duration/aperture combinations. At the start
of each run, we determine which targets are observable from each telescope given by looking up the
correct coefficients and calculating the minimum observable depth at that stellar magnitude.

If the telescope is capable, it is added to the approved list, which is checked
when scheduling observations to be observed at the telescopes.