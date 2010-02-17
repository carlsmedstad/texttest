
""" Simple interface to matplotlib """
from matplotlib import use
use("Agg") # set backend to one that doesn't need a DISPLAY
import plugins, pylab, logging, operator
from ndict import seqdict

class Graph:
    cms_per_inch = 2.54
    # Initiation of the class with default values
    def __init__(self, title, width, height):
        self.y_label = ''
        self.x_label = ''
        self.plotLabels = []
        self.legendItems = []
        # creating and set size of the graph
        pylab.clf()
        self.fig1 = pylab.figure(1)
        self.fig1.set_figwidth(width / self.cms_per_inch)
        self.fig1.set_figheight(height / self.cms_per_inch)
        self.sub1 = pylab.subplot(111)
        pylab.title(title, fontsize = 10, family='monospace')
                  
    def save(self, fn):
        self.finalise_graph()
        self.fig1.savefig(fn, dpi=100)

    def addPlot(self, x_values, y_values, label, *args, **kw):
        self.plotLabels.append(label)
        return self.sub1.plot(x_values, y_values, label=label, *args, **kw)
        
    def addFilledRegion(self, x_values, old_y_values, y_values, label, color="", *args, **kw):
        self.sub1.set_autoscale_on(False)
        # Add an invisible line, so it can find where to put the legend
        l1, = self.addPlot(x_values, y_values, label, color=color, *args, **kw)
        l1.set_visible(False)
        self.sub1.set_autoscale_on(True)
        for subx, sub_old_y, suby in self.findFillRegions(x_values, old_y_values, y_values):
            if len(subx):
                self.sub1.fill_between(subx, sub_old_y, suby, color=color, *args, **kw)
        self.legendItems.append(pylab.Rectangle((0, 0), 1, 1, fc=color))

    def findFillRegions(self, x_values, old_y_values, y_values):
        lists = []
        lists.append(([], [], []))
        regions = [ (i, i + 1) for i in range(len(x_values) - 1) ]
        for index1, index2 in regions:
            if old_y_values[index1] == y_values[index1] and old_y_values[index2] == y_values[index2]:
                if len(lists[-1][0]):
                    lists.append(([], [], []))
            else:
                currX, currOldY, currY = lists[-1]
                if len(currX) > 0 and currX[-1] == index1:
                    indices = [ index2 ]
                else:
                    indices = [ index1, index2 ]
                for index in indices:
                    currX.append(x_values[index])
                    currOldY.append(old_y_values[index])
                    currY.append(y_values[index])
        return lists
        
    def setXticks(self, labelList):
        pylab.xticks(range(len(labelList)), labelList)
        pylab.setp(self.sub1.get_xticklabels(), 'rotation', 90, fontsize=7)

    def finalise_graph(self):
        leg = self.sub1.legend(self.legendItems, tuple(self.plotLabels), 'best', shadow=False)
        leg.get_frame().set_alpha(0.5) # transparent legend box		
        

class GraphGenerator:
    labels = seqdict()
    labels["success"] = "Succeeded tests"
    labels["performance"] = "Performance difference"
    labels["memory"] = "Memory difference"
    labels["knownbug"] = "Known Issues"
    labels["failure"] = "Failed tests"
    def __init__(self):
        self.diag = logging.getLogger("GenerateWebPages")
        self.diag.info("Generating graphs...")
        
    def generateGraph(self, fileName, graphTitle, results, colourFinder):
        print "Generating graph at " + fileName + " ..."
        graph = Graph(graphTitle, width=24, height=20)
        self.addAllPlots(graph, results, colourFinder)
        self.addDateLabels(graph, results)
        plugins.ensureDirExistsForFile(fileName)
        graph.save(fileName)

    def addAllPlots(self, graph, results, *args):
        prevYlist = [ 0 ] * len(results)
        plotData = seqdict()
        for category in self.labels.keys():
            currYlist = [ summary.get(category, 0) for tag, summary in results ]
            if self.hasNonZero(currYlist):
                ylist = [ (currYlist[x] + prevYlist[x]) for x in range(len(prevYlist)) ]
                plotData[category] = prevYlist, ylist
                prevYlist = ylist

        for category in reversed(plotData.keys()):
            prevYlist, ylist = plotData[category]
            self.addPlot(prevYlist, ylist, graph, category=category, *args)
        
    def hasNonZero(self, numbers):
        return reduce(operator.or_, numbers, False)

    def addPlot(self, prevYlist, ylist, graph, colourFinder, category=""):
        colour = colourFinder.find(category + "_bg")
        label = self.labels[category]
        self.diag.info("Creating plot '" + label + "', coloured " + colour)
        xlist = range(len(ylist))
        self.diag.info("Data to plot = " + repr(ylist))
        graph.addFilledRegion(xlist, prevYlist, ylist, label=label, linewidth=2, linestyle="-", color=colour)
        
    def addDateLabels(self, graph, results):
        xticks = []
        # Create list of x ticks
        numresults = len(results)
        # Interval between labels (10 labels in total, use '' between the labels)
        interval = max(numresults / 10, 1)
        for i, (tag, summary) in enumerate(results):
            if i % interval == 0:
                xticks.append(tag)
            else:
                xticks.append('')
        graph.setXticks(xticks)
