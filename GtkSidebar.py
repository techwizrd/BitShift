#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

class GtkSidebar(gtk.Frame):
    __gtype_name = 'GtkSidebar'
    def __init__(self):
        gtk.Frame.__init__(self)

        self.SBscrollbar = gtk.ScrolledWindow()
        self.SBscrollbar.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.SBstore = gtk.TreeStore(str, gtk.gdk.Pixbuf)
        self.SBtreeview = gtk.TreeView(self.SBstore)

        self.SBcolumn = gtk.TreeViewColumn('Pixbuf and Text')
        self.SBtreeview.append_column(self.SBcolumn)

        self.SBcell0 = gtk.CellRendererPixbuf()
        self.SBcell1 = gtk.CellRendererText()

        self.SBcolumn.pack_start(self.SBcell0, False)
        self.SBcolumn.pack_start(self.SBcell1, True)

        if gtk.gtk_version[1] < 2:
            self.SBcolumn.set_cell_data_func(self.SBcell0, self.make_pb)
        else:
            self.SBcolumn.set_attributes(self.SBcell0, pixbuf=1)#stock_id=1)
        self.SBcolumn.set_attributes(self.SBcell1, markup=0)

        self.SBtreeview.set_search_column(0)
        self.SBcolumn.set_sort_column_id(0)
        
        self.SBtreeview.set_headers_visible(False)

       # self.add(self.SBscrollbar)
        self.SBscrollbar.add(self.SBtreeview)

    def add_item(self, parent, stuff):
    	"""Add items to the model. If adding a large amount of items, decouple
    	first, add the items, and then recouple it."""
        return self.SBstore.append(parent, stuff)
    
    def decouple(self):
    	"""Used for decoupling the model. This is useful when adding large
    	amounts of rows, as you do not need to wait for each addition to
    	update the TreeView. Just remember to call recouple() afterwards."""
    	self.SBtreeview.set_model(None)
    
    def recouple(self):
    	"""Used for recoupling the model. This is useful when adding large
    	amounts of rows, as you do not need to wait for each addition to
    	update the TreeView."""
    	self.SBtreeview.set_model(self.SBstore)
    
    def make_pb(self, tvcolumn, cell, model, iter):
        stock = model.get_value(iter, 1)
        pb = self.SBtreeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
        cell.set_property('pixbuf', pb)
        return
    
    def get_store(self):
    	return self.SBstore
    	
    def clear(self):
    	self.decouple()
    	self.SBstore.clear()
    	self.recouple()
        
        
if __name__ == "__main__":
    a = gtk.Window()
    a.connect('delete_event', gtk.main_quit)
    a.set_size_request(200,400)
    b = GtkSidebar()
    a.add(b)
    a.show_all()
    for item in range(1, 6):
    	b.add_item(None, ['Parent %i' % item, None])
    for parent in range(6,11):
        piter = b.add_item(None, ['Parent %i' % parent, gtk.STOCK_OPEN])
        for child in range(1,6):
            b.add_item(piter, ['Child %i of Parent %i' % (child, parent), gtk.STOCK_NEW])
    gtk.main()

