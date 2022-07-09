#!/usr/bin/env python

import os, sys, re
import numpy as np
import pandas as pd
import matplotlib
# Unless this is set, the script may freeze while it attempts to use X windows
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

logfnms = sys.argv[1:]

if len(logfnms) == 0 or any([not os.path.exists(fnm) for fnm in logfnms]):
    print("Exiting because did not provide valid log filenames.")
    print("Usage: ./plot-performance.py <geomeTRIC log filenames>")
    sys.exit()
    
labels = input('Enter optional custom plot labels separated by space (%i required) --> ' % len(logfnms)).split()
if len(labels) != len(logfnms):
    print("Did not provide valid labels - using log filenames.")
    labels = [i.replace('.log', '') for i in logfnms]

df_energy = pd.DataFrame(dict([(label, []) for label in labels]))
df_grms = pd.DataFrame(dict([(label, []) for label in labels]))
df_gmax = pd.DataFrame(dict([(label, []) for label in labels]))
df_drms = pd.DataFrame(dict([(label, []) for label in labels]))
df_dmax = pd.DataFrame(dict([(label, []) for label in labels]))
df_qual = pd.DataFrame(dict([(label, []) for label in labels]))
status = {}

for ifnm, fnm in enumerate(logfnms):
    label = labels[ifnm]
    step = 0
    status[label] = "Unknown"
    for line in open(fnm):
        # Strip ANSI coloring
        line = re.sub(r'\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)*[m|K]','',line)
        if re.match('^Step +[0-9]+ :', line): # Line contains geom-opt. data
            if 'Gradient' in line: # This is the zero-th step
                grms_gmax_word = re.split('Gradient = ', line)[1].split()[0]
                grms, gmax = (float(i) for i in grms_gmax_word.split('/'))
                energy = float(line.split()[-1])
                df_energy.loc[step, label] = energy
                df_grms.loc[step, label] = grms
                df_gmax.loc[step, label] = gmax
                df_drms.loc[step, label] = np.nan
                df_dmax.loc[step, label] = np.nan
                df_qual.loc[step, label] = np.nan
            else:
                energy = float(re.split('E \(change\) = ', line)[1].split()[0])
                if "Grad_T" in line: # It's a constrained optimization
                    grms_gmax_word = re.split('Grad_T = ', line)[1].split()[0]
                else:
                    grms_gmax_word = re.split('Grad = ', line)[1].split()[0]
                grms, gmax = (float(i) for i in grms_gmax_word.split('/'))
                drms_dmax_word = re.split('Displace = ', line)[1].split()[0]
                drms, dmax = (float(i) for i in drms_dmax_word.split('/'))
                quality = float(line.split()[-1])
                df_energy.loc[step, label] = energy
                df_grms.loc[step, label] = grms
                df_gmax.loc[step, label] = gmax
                df_drms.loc[step, label] = drms
                df_dmax.loc[step, label] = dmax
                df_qual.loc[step, label] = quality
            step += 1
        if "Maximum iterations reached" in line:
            if status[label] not in ["Unknown", "MaxIter"]: print("Warning: Found multiple status messages")
            status[label] = "MaxIter"
        if "Converged!" in line:
            if status[label] not in ["Unknown", "Converged"]: print("Warning: Found multiple status messages")
            status[label] = "Converged"
        if "KeyboardInterrupt" in line:
            if status[label] not in ["Unknown", "Interrupted"]: print("Warning: Found multiple status messages")
            status[label] = "Interrupted"

def get_vmin_vmax_log(df, pad=0.2):
    vmin = 10**np.floor(np.log10(np.nanmin(df.replace(0, np.nan).values))-pad)
    vmax = 10**np.ceil(np.log10(np.nanmax(df.replace(0, np.nan).values))+pad)
    return vmin, vmax
    
if np.std(df_energy.iloc[0]) > 1e-6:
    print("--== Warning - step 0 energies are not all the same ==--")

# Convert raw energies to energy change from first frame in kcal/mol
df_energy_kcal = (df_energy - df_energy.iloc[0]).apply(lambda x: x*627.51)

with PdfPages('plot-performance.pdf') as pdf:
    # Plot the energy change
    fig, ax = plt.subplots()
    fig.set_size_inches((6, 5))
    ax.set_xlabel('Optimization Cycle')
    ax.set_ylabel('Energy change (kcal/mol)')
    df_energy_kcal.plot(ax=ax)
    labels = []
    for col in df_energy_kcal.columns:
        labels.append("%s %s N=%i" % (col, status[col], df_energy_kcal[col].last_valid_index()))
    ax.legend(labels)
    pdf.savefig(fig)
    plt.close()

    titles = ['RMS Gradient', 'Max Gradient', 'RMS Displacement', 'Max Displacement']
    dfs = [df_grms, df_gmax, df_drms, df_dmax]
    convs = [3.0e-4, 4.5e-4, 1.2e-3, 1.8e-3]
    for title, df, conv in zip(titles, dfs, convs):
        fig, ax = plt.subplots()
        fig.set_size_inches((6, 5))
        ax.set_xlabel('Optimization Cycle')
        ax.set_ylabel(title)
        vmin, vmax = get_vmin_vmax_log(df)
        df.plot(ax=ax, ylim=(vmin, vmax), logy=True)
        ax.legend(labels)
        ax.hlines(y=conv, xmin=0, xmax=df.shape[0], colors='k', linestyle='--')
        pdf.savefig(fig)
        plt.close()


