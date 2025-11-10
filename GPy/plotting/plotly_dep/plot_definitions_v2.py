#===============================================================================
# Copyright (c) 2015, Max Zwiessele
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of GPy.plotting.matplot_dep.plot_definitions nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#===============================================================================
import numpy as np
from GPy.plotting.abstract_plotting_library import AbstractPlottingLibrary
from GPy.plotting import Tango
from GPy.plotting.plotly_dep import defaults
import plotly
from plotly import subplots
from plotly.graph_objs import Scatter, Scatter3d,\
    Bar, Heatmap, Trace,\
    Contour, Surface, Marker
from plotly.graph_objs.scatter import Line, ErrorY, ErrorX
from plotly.graph_objs.layout import Font, Annotation
from _plotly_utils.exceptions import PlotlyDictKeyError

SYMBOL_MAP = {
    'o': 'circle-dot',
    'v': 'triangle-down',
    '^': 'triangle-up',
    '<': 'triangle-left',
    '>': 'triangle-right',
    's': 'square',
    '+': 'cross',
    'x': 'x',
    '*': 'star',
    'D': 'diamond',
    'd': 'diamond',
}

class PlotlyPlotsBase(AbstractPlottingLibrary):
    def __init__(self):
        super(PlotlyPlotsBase, self).__init__()
        self._defaults = defaults.__dict__
        self.current_states = dict()

    def figure(self, rows=1, cols=1, specs=None, is_3d=False, **kwargs):
        if specs is None:
            specs = [[{'type': 'scene'}]*cols]*rows
        figure = subplots.make_subplots(rows, cols, specs=specs, **kwargs)
        return figure

    def new_canvas(self, figure=None, row=1, col=1, projection='2d',
                   xlabel=None, ylabel=None, zlabel=None,
                   title=None, xlim=None,
                   ylim=None, zlim=None, **kwargs):
        #if 'filename' not in kwargs:
        #    print('PlotlyWarning: filename was not given, this may clutter your plotly workspace')
        #    filename = None
        #else:
        #    filename = kwargs.pop('filename')
        if figure is None:
            figure = self.figure(is_3d=projection=='3d')
            figure.layout.font = Font(family="Raleway, sans-serif")
        if projection == '3d':
            figure.layout.legend.x=.5
            figure.layout.legend.bgcolor='#DCDCDC'
        return (figure, row, col), kwargs

    def add_to_canvas(self, canvas, traces, legend=False, **kwargs):
        figure, row, col = canvas

        def append_trace(t, row, col):
            figure.add_trace(t, row=row, col=col)

        def recursive_append(traces):
            if isinstance(traces, (tuple, list)):
                if isinstance(traces[0], Annotation):
                    #figure.xref[row-1][col-1]
                    #yref = "y20 domain"#figure.yref[row-1][col-1]
                    for a in traces:
                        figure.add_annotation(arg=a, row=row, col=col)
                        if a.name  == "_add_domain":
                            figure.layout.annotations[-1].yref += " domain"
                else:
                    for t in traces:
                        recursive_append(t)
            # elif isinstance(traces, (Trace)):  # doesn't work
            # elif type(traces) in [v for k,v in go.__dict__.iteritems()]:
            elif isinstance(traces, (Scatter, Scatter3d, ErrorX,
                        ErrorY, Bar, Heatmap, Trace, Contour, Surface)):
                try:
                    append_trace(traces, row, col)
                except PlotlyDictKeyError:
                    # Its a dictionary of plots:
                    for t in traces:
                        recursive_append(traces[t])
            elif isinstance(traces, (dict)):
                for t in traces:
                    recursive_append(traces[t])

        recursive_append(traces)
        figure.layout['showlegend'] = legend
        return canvas

    def show_canvas(self, canvas, filename=None, **kwargs):
        return NotImplementedError

    def scatter(self, ax, X, Y, Z=None, color=Tango.colorsHex['mediumBlue'], cmap=None, label=None, marker='o', marker_kwargs=None, **kwargs):
        try:
            marker = SYMBOL_MAP[marker]
        except:
            #not matplotlib marker
            pass
        marker_kwargs = marker_kwargs or {}
        if 'symbol' not in marker_kwargs:
            marker_kwargs['symbol'] = marker
        X, Y = np.squeeze(X), np.squeeze(Y)
        if Z is not None:
            Z = np.squeeze(Z)
            return Scatter3d(x=X, y=Y, z=Z, mode='markers',
                             showlegend=label is not None,
                             marker=Marker(color=color, colorscale=cmap, **marker_kwargs),
                             name=label, **kwargs)
        return Scatter(x=X, y=Y, mode='markers', showlegend=label is not None,
                       marker=Marker(color=color, colorscale=cmap, **marker_kwargs),
                       name=label, **kwargs)

    def plot(self, ax, X, Y, Z=None, color=None, label=None, line_kwargs=None, **kwargs):
        if 'mode' not in kwargs:
            kwargs['mode'] = 'lines'
        X, Y = np.squeeze(X), np.squeeze(Y)
        if Z is not None:
            Z = np.squeeze(Z)
            return Scatter3d(x=X, y=Y, z=Z, showlegend=label is not None, line=Line(color=color, **line_kwargs or {}), name=label, **kwargs)
        return Scatter(x=X, y=Y, showlegend=label is not None, line=Line(color=color, **line_kwargs or {}), name=label, **kwargs)

    def plot_axis_lines(self, ax, X, color=Tango.colorsHex['mediumBlue'], label=None, marker_kwargs=None, **kwargs):
        if X.shape[1] == 1:
            annotations = []
            for i, row in enumerate(X):
                annotation = Annotation(
                    text='',
                    x=row[0], y=0,
                    ax=0, ay=20,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=color,
                    showarrow=True,
                    name = "_add_domain"
                    )
                annotations.append(annotation)
            return annotations
        elif X.shape[1] == 2:
            marker_kwargs.setdefault('symbol', 'diamond')
            opacity = kwargs.pop('opacity', .8)
            return Scatter3d(x=X[:, 0], y=X[:, 1], z=np.zeros(X.shape[0]),
                             mode='markers',
                             projection=dict(z=dict(show=True, opacity=opacity)),
                             marker=Marker(color=color, **marker_kwargs or {}),
                             opacity=0,
                             name=label,
                             showlegend=label is not None, **kwargs)

    def barplot(self, canvas, x, height, width=0.8, bottom=0, color=Tango.colorsHex['mediumBlue'], label=None, **kwargs):
        figure, _, _ = canvas
        if 'barmode' in kwargs:
            figure.layout['barmode'] = kwargs.pop('barmode')
        return Bar(x=x, y=height, marker=Marker(color=color), name=label)

    def xerrorbar(self, ax, X, Y, error, Z=None, color=Tango.colorsHex['mediumBlue'], label=None, error_kwargs=None, **kwargs):
        error_kwargs = error_kwargs or {}
        if (error.shape[0] == 2) and (error.ndim == 2):
            error_kwargs.update(dict(array=error[1], arrayminus=error[0], symmetric=False))
        else:
            error_kwargs.update(dict(array=error, symmetric=True))
        X, Y = np.squeeze(X), np.squeeze(Y)
        if Z is not None:
            Z = np.squeeze(Z)
            return Scatter3d(x=X, y=Y, z=Z, mode='markers',
                             error_x=ErrorX(color=color, **error_kwargs or {}),
                             marker=Marker(size=0), name=label,
                             showlegend=label is not None, **kwargs)
        return Scatter(x=X, y=Y, mode='markers',
                       error_x=ErrorX(color=color, **error_kwargs or {}),
                       marker=Marker(size=0), name=label,
                      showlegend=label is not None,
                       **kwargs)

    def yerrorbar(self, ax, X, Y, error, Z=None, color=Tango.colorsHex['mediumBlue'], label=None, error_kwargs=None, **kwargs):
        error_kwargs = error_kwargs or {}
        if (error.shape[0] == 2) and (error.ndim == 2):
            error_kwargs.update(dict(array=error[1], arrayminus=error[0], symmetric=False))
        else:
            error_kwargs.update(dict(array=error, symmetric=True))
        X, Y = np.squeeze(X), np.squeeze(Y)
        if Z is not None:
            Z = np.squeeze(Z)
            return Scatter3d(x=X, y=Y, z=Z, mode='markers',
                             error_y=ErrorY(color=color, **error_kwargs or {}),
                             marker=Marker(size=0), name=label,
                             showlegend=label is not None, **kwargs)
        return Scatter(x=X, y=Y, mode='markers',
                       error_y=ErrorY(color=color, **error_kwargs or {}),
                       marker=Marker(size=0), name=label,
                      showlegend=label is not None,
                       **kwargs)

    def imshow(self, ax, X, extent=None, label=None, vmin=None, vmax=None, **imshow_kwargs):
        if not 'showscale' in imshow_kwargs:
            imshow_kwargs['showscale'] = False
        if extent == None:
            extent = (0, (X.shape[0]-1), 0, (X.shape[1]-1))
        return Heatmap(z=X, name=label,
                       x0=extent[0], dx=float(extent[1]-extent[0])/(X.shape[0]-1),
                       y0=extent[2], dy=float(extent[3]-extent[2])/(X.shape[1]-1),
                       zmin=vmin, zmax=vmax,
                       showlegend=label is not None,
                       hoverinfo='z',
                       **imshow_kwargs)

    def imshow_interact(self, ax, plot_function, extent=None, label=None, resolution=None, vmin=None, vmax=None, **imshow_kwargs):
        # TODO stream interaction?
        super(PlotlyPlotsBase, self).imshow_interact(ax, plot_function)

    def annotation_heatmap(self, ax, X, annotation, extent=None, label='Gradient', imshow_kwargs=None, **annotation_kwargs):
        if imshow_kwargs is None:
            imshow_kwargs = {}
        imshow_kwargs.setdefault('label', label)
        imshow_kwargs.setdefault('showscale', True)
        if extent == None:
            extent = (0, (X.shape[0]-1), 0, (X.shape[1]-1))
        imshow = self.imshow(ax, X, extent, **imshow_kwargs)
        X = X-X.min()
        X /= X.max()/2.
        X -= 1
        x = np.linspace(extent[0], extent[1], X.shape[0])
        y = np.linspace(extent[2], extent[3], X.shape[1])
        annotations = []
        for n, row in enumerate(annotation):
            for m, val in enumerate(row):
                var = X[n][m]
                annotations.append(
                    Annotation(
                        text=str(val),
                        x=x[m], y=y[n],
                        xref='x1', yref='y1',
                        font=dict(color='white' if np.abs(var) > 0.8 else 'black', size=10),
                        opacity=.5,
                        showarrow=False,
                        ))
        return imshow, annotations

    def annotation_heatmap_interact(self, ax, plot_function, extent, label=None, resolution=15, imshow_kwargs=None, **annotation_kwargs):
        super(PlotlyPlotsBase, self).annotation_heatmap_interact(ax, plot_function, extent)

    def contour(self, ax, X, Y, C, levels=20, label=None, **kwargs):
        return Contour(x=X, y=Y, z=C,
                       #ncontours=levels, contours=Contours(start=C.min(), end=C.max(), size=(C.max()-C.min())/levels),
                       name=label, **kwargs)

    def surface(self, ax, X, Y, Z, color=None, label=None, **kwargs):
        return Surface(x=X, y=Y, z=Z, name=label, showlegend=label is not None, **kwargs)



if __name__ == "__main__":
    import plotly.graph_objects as go
    import numpy as np
    plot = PlotlyPlotsBase()
    if 0:
        fig = plot.figure(rows = 2, cols = 2)
        #Make new canvas to draw subplots on
        canvas, kwargs = plot.new_canvas(figure=fig)
        x = [1,2,3]
        y = [3,2,6]
        y2 = [4,5,2]
        trace = go.Scatter(x=x,y=y)
        fig, row, col = canvas
        plot_trace = plot.plot(None, x, y2)
        xerror = np.array([0.2,0.4,0.1]).reshape(-1,1)
        error_trace = plot.xerrorbar(None, x, y, xerror)
        new_canvas = plot.add_to_canvas(canvas, [trace, plot_trace, error_trace])
        #make another canvas
        canvas2 = (fig, row+1, col)
        trace2 = plot.scatter(None, x, y)
        x_lines = np.array([1.2,2.4,2.9]).reshape(-1,1)
        axis_lines = plot.plot_axis_lines(None, x_lines)
        new_canvas2 = plot.add_to_canvas(canvas2, [trace2, axis_lines])
        new_fig, new_row, new_col = new_canvas2
        #make a barplot canvas
        canvas3 = (fig, 1, 2)
        bar_trace = plot.barplot(canvas3, x, y)
        yerrors = np.array([0.1,0.3,0.2]).reshape(-1,1)
        yerror_trace = plot.yerrorbar(None, x, y, yerrors)
        new_canvas3 = plot.add_to_canvas(canvas3, [bar_trace, axis_lines, yerror_trace])
        #Make a heatmap canvas
        canvas4 = (fig, 2, 2)
        heat_data = np.random.sample((10,10))
        annotatium = np.array([["Goblium"]*10]*10)
        heat_trace = plot.annotation_heatmap(None, heat_data, annotatium)
        plot.add_to_canvas(canvas4, [heat_trace])
        print(fig)
        fig.show()

    #more stuff
    specs = np.array([[{"type" : "xy"}]*2]*2)
    specs[1,0] = {"type" : "scene"}
    specs = specs.tolist()
    print(specs)
    fig = plot.figure(rows = 2, cols = 2, specs = specs)
    print(fig)
    #contour canvas
    canvas, kwargs = plot.new_canvas(figure=fig)
    x = np.linspace(0,10,11)
    y = np.linspace(0,10,11)
    def foo(x,y):
        return np.exp(-(x-5)**2-(y-5)**2)/(2*np.pi)
    X, Y = np.meshgrid(x,y)
    Z = foo(X,Y)
    cont_trace = plot.contour(None, x, y, Z)
    plot.add_to_canvas(canvas,cont_trace)
    #surface canvas
    surface_canvas = (fig, 2, 1)
    #surface_canvas, kwargs = plot.new_canvas(figure=fig, row=2, col=1, projection='3d')
    surface_trace = plot.surface(None,x,y,Z)
    plot.add_to_canvas(surface_canvas,surface_trace)

    fig.show()
