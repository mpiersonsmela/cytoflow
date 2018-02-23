'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.view_plugins.bar_chart import BarChartPlugin, BarChartPlotParams
from cytoflowgui.subset import CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml, traits_eq, traits_hash

class TestBarchart(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = ChannelStatisticPlugin()
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.SD"
        op.by = ['Dox', 'Well']

        wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.Mean"
        op.by = ['Dox', 'Well']
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 10))
        
        plugin = BarChartPlugin()
        self.view = view = plugin.get_view()
        view.statistic = ("MeanByDox", "Geom.Mean")
        view.variable = "Dox"
        view.huefacet = "Well"
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
  
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


    def testPlot(self):
        pass
     
 
    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
  
        self.view.yscale = "log"
          
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.huefacet = ""
        self.view.xfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
 
         
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.huefacet = ""
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testErrorBars(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.error_statistic = ("MeanByDox", "Geom.SD")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

    def testPlotArgs(self):
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.error_statistic = ("MeanByDox", "Geom.SD")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.title = "Title"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.xlabel = "X label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.ylabel = "Y label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharex = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharey = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.despine = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = ""
        self.view.huefacet = "Well"
        self.view.plot_params.huelabel = "Hue label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.legend = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        ## stats1d-specific params
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.orientation = "horizontal"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.errwidth = 2
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.capsize = 5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

 
    def testSerialize(self):
        BarChartPlotParams.__eq__ = traits_eq
        BarChartPlotParams.__hash__ = traits_hash
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
               
            save_yaml(self.view, filename)
            new_view = load_yaml(filename)
               
        finally:
            os.unlink(filename)
               
        self.maxDiff = None
                        
        self.assertDictEqual(self.view.trait_get(self.view.copyable_trait_names()),
                             new_view.trait_get(self.view.copyable_trait_names()))
           
           
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
           
        exec(code) # smoke test


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestBarchart.testSerialize']
    unittest.main()