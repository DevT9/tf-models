"""Intersection over union calculation utils."""

# Import libraries
import tensorflow as tf
import math

from official.vision.beta.projects.yolo.ops import box_ops 



def compute_iou(box1, box2, xywh = True):
    """Calculates the intersection of union between box1 and box2.
    Args:
        box1: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
        box2: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
    Returns:
        iou: a `Tensor` who represents the intersection over union.
    """
    # get box corners
    with tf.name_scope("iou"):
        if xywh:
            box1 = box_ops.xcycwh_to_yxyx(box1)
            box2 = box_ops.xcycwh_to_yxyx(box2)
        intersection, union = box_ops.intersection_and_union(box1, box2)

        iou = tf.math.divide_no_nan(intersection, union)
        iou = tf.clip_by_value(iou, clip_value_min=0.0, clip_value_max=1.0)
    return iou


def compute_giou(box1, box2, xywh = True):
    """Calculates the generalized intersection of union between box1 and box2.
    Args:
        box1: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
        box2: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
    Returns:
        iou: a `Tensor` who represents the generalized intersection over union.
    """
    with tf.name_scope("giou"):
        # get box corners
        if xywh:
            box1 = box_ops.xcycwh_to_yxyx(box1)
            box2 = box_ops.xcycwh_to_yxyx(box2)

        # compute IOU
        intersection, union = box_ops.intersection_and_union(box1, box2)
        iou = tf.math.divide_no_nan(intersection, union)
        iou = tf.clip_by_value(iou, clip_value_min=0.0, clip_value_max=1.0)

        # find the smallest box to encompase both box1 and box2
        c_mins = tf.math.minimum(box1[..., 0:2], box2[..., 0:2])
        c_maxes = tf.math.maximum(box1[..., 2:4], box2[..., 2:4])
        c = box_ops.get_area((c_mins, c_maxes), use_tuple=True)

        # compute giou
        giou = iou - tf.math.divide_no_nan((c - union), c)
    return iou, giou


def compute_diou(box1, box2, xywh = True):
    """Calculates the distance intersection of union between box1 and box2.
    Args:
        box1: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
        box2: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
    Returns:
        iou: a `Tensor` who represents the distance intersection over union.
    """
    with tf.name_scope("diou"):
        

        # get box corners
        if xywh:
            box1 = box_ops.xcycwh_to_yxyx(box1)
            box2 = box_ops.xcycwh_to_yxyx(box2)
        
        # compute center distance
        dist = box_ops.center_distance((box1[..., 0:2] + box1[..., 2:4])/2, (box2[..., 0:2] + box2[..., 2:4])/2)

        # compute IOU
        intersection, union = box_ops.intersection_and_union(box1, box2)
        iou = tf.math.divide_no_nan(intersection, union)
        iou = tf.clip_by_value(iou, clip_value_min=0.0, clip_value_max=1.0)

        # compute max diagnal of the smallest enclosing box
        c_mins = tf.math.minimum(box1[..., 0:2], box2[..., 0:2])
        c_maxes = tf.math.maximum(box1[..., 2:4], box2[..., 2:4])
        diag_dist = box_ops.center_distance(c_mins, c_maxes)

        regularization = tf.math.divide_no_nan(dist, diag_dist)
        diou = iou + regularization
    return iou, diou


def compute_ciou(box1, box2, xywh = True):
    """Calculates the complete intersection of union between box1 and box2.
    Args:
        box1: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
        box2: a `Tensor` whose last dimension is 4 representing the coordinates of boxes in
            x_center, y_center, width, height.
    Returns:
        iou: a `Tensor` who represents the complete intersection over union.
    """
    with tf.name_scope("ciou"):
        #compute DIOU and IOU
        iou, diou = compute_diou(box1, box2, xywh = xywh)

        # computer aspect ratio consistency
        if not xywh:
            box1 = box_ops.xcycwh_to_yxyx(box1)
            box2 = box_ops.xcycwh_to_yxyx(box2)
        v = box_ops.aspect_ratio_consistancy(box1[..., 2], box1[..., 3], box2[..., 2],box2[..., 3])

        # compute IOU regularization
        a = tf.math.divide_no_nan(v, ((1 - iou) + v))
        ciou = diou + v * a
    return iou, ciou