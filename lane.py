import cv2
import numpy as np
import edge_detection as edge

# Global variables
prev_left_x = None
prev_left_y = None
prev_right_x = None
prev_right_y = None
prev_left_fit = []
prev_right_fit = []

prev_left_x2 = None
prev_left_y2 = None
prev_right_x2 = None
prev_right_y2 = None
prev_left_fit2 = []
prev_right_fit2 = []


class Lane:
    def __init__(self, orig_frame):
        self.orig_frame = orig_frame

        # This will hold an image with the lane lines
        self.lane_line_markings = None

        # This will hold the image after perspective transformation
        self.warped_frame = None
        self.transformation_matrix = None
        self.inv_transformation_matrix = None

        # (Width, Height) of the original video frame (or image)
        self.orig_image_size = self.orig_frame.shape[::-1][1:]

        width = self.orig_image_size[0]
        height = self.orig_image_size[1]
        self.width = width
        self.height = height

        # Four corners of the trapezoid-shaped region of interest
        self.roi_points = np.float32([
            (int(0.456 * width), int(0.544 * height)),  # Top-left corner
            (0, height - 1),  # Bottom-left corner
            (int(0.958 * width), height - 1),  # Bottom-right corner
            (int(0.6183 * width), int(0.544 * height))  # Top-right corner
        ])

        # The desired corner locations  of the region of interest
        # after performing perspective transformation.
        self.padding = int(0.25 * width)
        self.desired_roi_points = np.float32([
            [self.padding, 0],  # Top-left corner
            [self.padding, self.orig_image_size[1]],  # Bottom-left corner
            [self.orig_image_size[
                 0] - self.padding, self.orig_image_size[1]],  # Bottom-right corner
            [self.orig_image_size[0] - self.padding, 0]  # Top-right corner
        ])

        # Histogram that shows the white pixel peaks for lane line detection
        self.histogram = None

        # Sliding window parameters
        self.no_of_windows = 10
        self.margin = int((1 / 12) * width)  # Window width is +/- margin

        # Min no. of pixels to recenter window
        self.minpix = int((1 / 24) * width)

        # Best fit polynomial lines for left line and right line of the lane
        self.left_fit = None
        self.right_fit = None
        self.left_lane_inds = None
        self.right_lane_inds = None
        self.ploty = None
        self.left_fitx = None
        self.right_fitx = None
        self.leftx = None
        self.rightx = None
        self.lefty = None
        self.righty = None

        # Pixel parameters for x and y dimensions
        self.YM_PER_PIX = 7.0 / 400  # meters per pixel in y dimension
        self.XM_PER_PIX = 3.7 / 255  # meters per pixel in x dimension

        # Radii of curvature and offset
        self.left_curvem = None
        self.right_curvem = None
        self.center_offset = None

    def calculate_car_position(self):
        # Get position of car in centimeters
        car_location = self.orig_frame.shape[1] / 2

        # Fine the x coordinate of the lane line bottom
        height = self.orig_frame.shape[0]
        bottom_left = self.left_fit[0] * height ** 2 + self.left_fit[
            1] * height + self.left_fit[2]
        bottom_right = self.right_fit[0] * height ** 2 + self.right_fit[
            1] * height + self.right_fit[2]

        center_lane = (bottom_right - bottom_left) / 2 + bottom_left
        center_offset = (np.abs(car_location) - np.abs(
            center_lane)) * self.XM_PER_PIX * 100

        center = (abs(self.desired_roi_points[1][0] - self.desired_roi_points[2][0]) // 2) + int(
            self.desired_roi_points[1][0])

        self.center_offset = center_offset
        return center_offset, center

    def calculate_histogram(self, frame=None):
        if frame is None:
            frame = self.warped_frame

        # Generate the histogram
        self.histogram = np.sum(frame[int(
            frame.shape[0] / 2):, :], axis=0)

        return self.histogram

    def get_lane_line_previous_window(self, left_fit, right_fit):
        # margin is a sliding window parameter
        margin = self.margin

        # Find the x and y coordinates of all the nonzero
        nonzero = self.warped_frame.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])

        # Store left and right lane pixel indices
        left_lane_inds = ((nonzerox > (left_fit[0] * (nonzeroy ** 2) + left_fit[1] * nonzeroy + left_fit[2] - margin)) &
                          (nonzerox < (left_fit[0] * (nonzeroy ** 2) + left_fit[1] * nonzeroy + left_fit[2] + margin)))
        right_lane_inds = ((nonzerox > (right_fit[0] * (nonzeroy ** 2) + right_fit[1] * nonzeroy + right_fit[2] - margin))
                           & (nonzerox < (right_fit[0] * (nonzeroy ** 2) + right_fit[1] * nonzeroy + right_fit[2] + margin)))
        self.left_lane_inds = left_lane_inds
        self.right_lane_inds = right_lane_inds

        # Get the left and right lane line pixel locations
        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds]
        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds]

        global prev_left_x2
        global prev_left_y2
        global prev_right_x2
        global prev_right_y2
        global prev_left_fit2
        global prev_right_fit2

        # Make sure we have nonzero pixels
        if len(leftx) == 0 or len(lefty) == 0 or len(rightx) == 0 or len(righty) == 0:
            leftx = prev_left_x2
            lefty = prev_left_y2
            rightx = prev_right_x2
            righty = prev_right_y2

        self.leftx = leftx
        self.rightx = rightx
        self.lefty = lefty
        self.righty = righty

        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)

        # Add the latest polynomial coefficients
        prev_left_fit2.append(left_fit)
        prev_right_fit2.append(right_fit)

        # Calculate the moving average
        if len(prev_left_fit2) > 10:
            prev_left_fit2.pop(0)
            prev_right_fit2.pop(0)
            left_fit = sum(prev_left_fit2) / len(prev_left_fit2)
            right_fit = sum(prev_right_fit2) / len(prev_right_fit2)

        self.left_fit = left_fit
        self.right_fit = right_fit

        prev_left_x2 = leftx
        prev_left_y2 = lefty
        prev_right_x2 = rightx
        prev_right_y2 = righty

        # Create the x and y values to plot on the image
        ploty = np.linspace(
            0, self.warped_frame.shape[0] - 1, self.warped_frame.shape[0])
        left_fitx = left_fit[0] * ploty ** 2 + left_fit[1] * ploty + left_fit[2]
        right_fitx = right_fit[0] * ploty ** 2 + right_fit[1] * ploty + right_fit[2]
        self.ploty = ploty
        self.left_fitx = left_fitx
        self.right_fitx = right_fitx

    def get_lane_line_indices_sliding_windows(self):
        # Sliding window width is +/- margin
        margin = self.margin

        frame_sliding_window = self.warped_frame.copy()

        # Set the height of the sliding windows
        window_height = np.int(self.warped_frame.shape[0] / self.no_of_windows)

        # Find the x and y coordinates of all the nonzero
        # (i.e. white) pixels in the frame.
        nonzero = self.warped_frame.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])

        # Store the pixel indices for the left and right lane lines
        left_lane_inds = []
        right_lane_inds = []

        # Current positions for pixel indices for each window,
        # which we will continue to update
        leftx_base, rightx_base = self.histogram_peak()
        leftx_current = leftx_base
        rightx_current = rightx_base

        # Go through one window at a time
        no_of_windows = self.no_of_windows

        for window in range(no_of_windows):

            # Identify window boundaries in x and y (and right and left)
            win_y_low = self.warped_frame.shape[0] - \
                        (window + 1) * window_height
            win_y_high = self.warped_frame.shape[0] - window * window_height
            win_xleft_low = leftx_current - margin
            win_xleft_high = leftx_current + margin
            win_xright_low = rightx_current - margin
            win_xright_high = rightx_current + margin

            cv2.rectangle(frame_sliding_window, (win_xleft_low, win_y_low), (
                win_xleft_high, win_y_high), (255, 255, 255), 2)
            cv2.rectangle(frame_sliding_window, (win_xright_low, win_y_low), (
                win_xright_high, win_y_high), (255, 255, 255), 2)

            # Identify the nonzero pixels in x and y within the window
            good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                              (nonzerox >= win_xleft_low) & (
                                      nonzerox < win_xleft_high)).nonzero()[0]
            good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                               (nonzerox >= win_xright_low) & (
                                       nonzerox < win_xright_high)).nonzero()[0]

            # Append these indices to the lists
            left_lane_inds.append(good_left_inds)
            right_lane_inds.append(good_right_inds)

            # If you found > minpix pixels, recenter next window on mean position
            minpix = self.minpix
            if len(good_left_inds) > minpix:
                leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
            if len(good_right_inds) > minpix:
                rightx_current = np.int(np.mean(nonzerox[good_right_inds]))

        # Concatenate the arrays of indices
        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)

        # Extract the pixel coordinates for the left and right lane lines
        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds]
        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds]

        # Fit a second order polynomial curve to the pixel coordinates for
        # the left and right lane lines
        left_fit = None
        right_fit = None

        global prev_left_x
        global prev_left_y
        global prev_right_x
        global prev_right_y
        global prev_left_fit
        global prev_right_fit

        # Make sure we have nonzero pixels
        if len(leftx) == 0 or len(lefty) == 0 or len(rightx) == 0 or len(righty) == 0:
            leftx = prev_left_x
            lefty = prev_left_y
            rightx = prev_right_x
            righty = prev_right_y
        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)

        # Add the latest polynomial coefficients
        prev_left_fit.append(left_fit)
        prev_right_fit.append(right_fit)

        # Calculate the moving average
        if len(prev_left_fit) > 10:
            prev_left_fit.pop(0)
            prev_right_fit.pop(0)
            left_fit = sum(prev_left_fit) / len(prev_left_fit)
            right_fit = sum(prev_right_fit) / len(prev_right_fit)

        self.left_fit = left_fit
        self.right_fit = right_fit

        prev_left_x = leftx
        prev_left_y = lefty
        prev_right_x = rightx
        prev_right_y = righty
        return self.left_fit, self.right_fit

    def get_line_markings(self, frame=None):
        if frame is None:
            frame = self.orig_frame

        # Convert the video frame from BGR (blue, green, red)
        # color space to HLS (hue, saturation, lightness).
        hls = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)

        # Isolate possible lane line edges
        _, sxbinary = edge.threshold(hls[:, :, 1], thresh=(120, 255))
        sxbinary = edge.blur_gaussian(sxbinary, k_size=3)  # Reduce noise

        # 1s will be in the cells with the highest Sobel derivative values
        sxbinary = edge.mag_thresh(sxbinary, sobel_kernel=3, thresh=(110, 255))

        # Isolate possible lane lines
        s_channel = hls[:, :, 2]  # use only the saturation channel data
        _, s_binary = edge.threshold(s_channel, (130, 255))

        # Perform binary thresholding on the R (red) channel of the
        # original BGR video frame.
        _, r_thresh = edge.threshold(frame[:, :, 2], thresh=(120, 255))

        # Bitwise AND operation to reduce noise and black-out any pixels that
        # don't appear to be nice, pure, solid colors
        rs_binary = cv2.bitwise_and(s_binary, r_thresh)

        # Combine the possible lane lines with the possible lane line edges
        self.lane_line_markings = cv2.bitwise_or(rs_binary, sxbinary.astype(
            np.uint8))
        return self.lane_line_markings

    def histogram_peak(self):
        midpoint = np.int(self.histogram.shape[0] / 2)
        leftx_base = np.argmax(self.histogram[:midpoint])
        rightx_base = np.argmax(self.histogram[midpoint:]) + midpoint

        # (x coordinate of left peak, x coordinate of right peak)
        return leftx_base, rightx_base

    def overlay_lane_lines(self):
        # Generate an image to draw the lane lines on
        warp_zero = np.zeros_like(self.warped_frame).astype(np.uint8)
        color_warp = np.dstack((warp_zero, warp_zero, warp_zero))

        # Recast the x and y points into usable format for cv2.fillPoly()
        pts_left = np.array([np.transpose(np.vstack([
            self.left_fitx, self.ploty]))])
        pts_right = np.array([np.flipud(np.transpose(np.vstack([
            self.right_fitx, self.ploty])))])
        pts = np.hstack((pts_left, pts_right))

        # Draw lane on the warped blank image
        cv2.fillPoly(color_warp, np.int_([pts]), (0, 255, 0))

        # Warp the blank back to original image space using inverse perspective
        # matrix (Minv)
        newwarp = cv2.warpPerspective(color_warp, self.inv_transformation_matrix, (
            self.orig_frame.shape[
                1], self.orig_frame.shape[0]))

        # Combine the result with the original image
        result = cv2.addWeighted(self.orig_frame, 1, newwarp, 0.3, 0)

        return result

    def perspective_transform(self, frame=None):
        if frame is None:
            frame = self.lane_line_markings

        # Calculate the transformation matrix
        self.transformation_matrix = cv2.getPerspectiveTransform(
            self.roi_points, self.desired_roi_points)

        # Calculate the inverse transformation matrix
        self.inv_transformation_matrix = cv2.getPerspectiveTransform(
            self.desired_roi_points, self.roi_points)

        # Perform the transform using the transformation matrix
        self.warped_frame = cv2.warpPerspective(
            frame, self.transformation_matrix, self.orig_image_size, flags=(
                cv2.INTER_LINEAR))

        # Convert image to binary
        (thresh, binary_warped) = cv2.threshold(
            self.warped_frame, 127, 255, cv2.THRESH_BINARY)
        self.warped_frame = binary_warped
        return self.warped_frame
