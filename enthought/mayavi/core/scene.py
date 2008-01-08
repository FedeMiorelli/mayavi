"""A scene object manages a TVTK scene and objects in it.

"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005,  Enthought, Inc.
# License: BSD Style.

# Enthought library imports.
from enthought.traits.api import HasTraits, Instance, List, Str, Property
from enthought.traits.ui.api import View, Group, Item
from enthought.pyface.tvtk.scene import Scene
from enthought.persistence.state_pickler import set_state

# Local imports.
from enthought.mayavi.core.base import Base
from enthought.mayavi.core.source import Source
from enthought.mayavi.core.common import handle_children_state, exception


######################################################################
# `Scene` class.
######################################################################
class Scene(Base):

    # The version of this class.  Used for persistence.
    __version__ = 0

    # The source objects associated with this object.
    children = List(Source)

    # The name of this scene.
    name = Str('TVTK Scene')

    # The icon
    icon = Str('scene.ico')

    # The human-readable type for this object
    type = Str(' scene')

    # The objects view.
    view = View(Group(Item(name='scene', style='custom'), show_labels=False) )


    ######################################################################
    # `object` interface
    ######################################################################
    def __get_pure_state__(self):
        # Base removes the scene, but we need to save it!
        d = super(Scene, self).__get_pure_state__()
        d['scene'] = self.scene
        # Don't pickle the name.
        d.pop('name', None)
        return d

    def __set_pure_state__(self, state):
        handle_children_state(self.children, state.children)
        # Now set our complete state.  Doing the scene last ensures
        # that the camera view is set right.
        set_state(self, state, last=['scene'])

    ######################################################################
    # `Base` interface
    ######################################################################
    def start(self):
        """This is invoked when this object is added to the mayavi
        pipeline.
        """
        # Do nothing if we are already running.
        if self.running:
            return
        
        # Start all our children.
        for obj in self.children:
            obj.start()

        # Disallow the hide action in the context menu
        self._HideShowAction.enabled = False

        super(Scene, self).start()

    def stop(self):
        """Invoked when this object is removed from the mayavi
        pipeline.
        """
        if not self.running:
            return

        # Disable rendering to accelerate shutting down.
        scene = self.scene
        if scene is not None:
            status = scene.disable_render
            scene.disable_render = True
        try:
            # Stop all our children.
            for obj in self.children:
                obj.stop()
        finally:
            # Re-enable rendering.
            if scene is not None:
                scene.disable_render = status
            
        super(Scene, self).stop()

    def add_child(self, child):
        """This method intelligently adds a child to this object in
        the MayaVi pipeline.        
        """
        self.children.append(child)
    
    ######################################################################
    # `TreeNodeObject` interface
    ######################################################################
    def tno_can_add(self, node, add_object):
        """ Returns whether a given object is droppable on the node.
        """
        try:
            if issubclass(add_object, Source):
                return True
        except TypeError:
            if isinstance(add_object, Source):
                return True
        return False

    def tno_drop_object(self, node, dropped_object):
        """ Returns a droppable version of a specified object.
        """
        if isinstance(dropped_object, Source):
            return dropped_object
   
    ######################################################################
    # Non-public interface
    ######################################################################
    def _children_changed(self, old, new):
        self._handle_children(old, new)

    def _children_items_changed(self, list_event):
        self._handle_children(list_event.removed, list_event.added)            
    
    def _handle_children(self, removed, added):
        for obj in removed:
            obj.stop()
        for obj in added:
            obj.scene = self.scene
            if self.running:
                # It makes sense to start children only if we are running.
                # If not, the children will be started when we start.
                try:
                    obj.start()
                except:
                    exception()
            