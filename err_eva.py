import os
import cv2
import numpy as np

class calibrator():
    def __init__(self, img):
        self.img = img
        self.img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        self.img_red = self.hsv_filter(self.img_hsv, "red")
        self.is_red = True
        self.corner_points = []
        self.get_real_shape()

    def get_real_shape(self):
        # print("Please enter the width of the red pts rectangle (in your desired unit)")
        # self.width = float(input("Width: "))
        # print("Please enter the height of the red pts rectangle (in your desired unit)")
        # self.height = float(input("Height: "))
        # print("Please enter the distance between the blue pts(in your desired unit)")
        # self.distance = float(input("Distance: "))
        self.width = 172.2
        self.height = 114.8
        self.distance = 14.65

        nh, nw = (7, 11)
        hh = np.linspace(-self.distance*3, self.distance*3, nh)
        ww = np.linspace(-self.distance*5, self.distance*5, nw)
        self.ref_pts = np.array([[x, y] for x in ww for y in hh])

    def hsv_filter(self, img_hsv, mode = "red"):
        blue_low = np.array([64, 0, 30])
        blue_high = np.array([128, 255, 128])

        red_low_1 = np.array([0, 70, 50])
        red_high_1 = np.array([10, 255, 255])
        red_low_2 = np.array([170, 70, 50])
        red_high_2 = np.array([180, 255, 255])

        if mode == "red":
            mask_red_1 = cv2.inRange(img_hsv, red_low_1, red_high_1)
            mask_red_2 = cv2.inRange(img_hsv, red_low_2, red_high_2)
            mask_red = cv2.bitwise_or(mask_red_1, mask_red_2)
            return mask_red
        elif mode == "blue":
            mask_blue = cv2.inRange(img_hsv, blue_low, blue_high)
            return mask_blue
        else:
            print("Invalid mode")
            return None
        
    def find_centers(self, masked):
        contours, _ = cv2.findContours(masked, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        centers = []
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centers.append((cx, cy))
        return centers
    
    def match_centers(self, pts, centers):
        pts = np.atleast_2d(np.array(pts))      
        re_pts = []
        for pt in pts:
            for center in centers:
                dis = (pt[0] - center[0])**2 + (pt[1] - center[1])**2
                if dis < 25:
                    re_pts.append(center)
        return re_pts
    
    def warp_image(self, corners):
        height, width = self.img.shape[:2]
        
        dst_pts = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype='float32')
        
        M = cv2.getPerspectiveTransform(np.array(corners, dtype='float32'), dst_pts)
        warped = cv2.warpPerspective(self.img, M, (width, height))
        return warped
    
    def cal_error(self):
        h, w = self.wraped.shape[:2]
        ratio_w = self.width / w
        ratio_h = self.height / h
        real_pos = (self.centor_pts-self.middle_pts) * np.array([ratio_w, ratio_h])
        
        D = np.sum((real_pos[:, np.newaxis, :] - self.ref_pts[np.newaxis, :, :]) ** 2, axis=2)
        self.error = np.sqrt(np.min(D, axis=1))
            
    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print("LB Clicked")
            if self.is_red:
                self.corner_points.append((x, y))
            if len(self.corner_points) == 4:
                print("Red corner points are set")
                self.is_red = False

                # match the corner points centers
                hsv_red = self.hsv_filter(self.img_hsv, "red")
                centers = self.find_centers(hsv_red)
                corners = self.match_centers(self.corner_points, centers)

                self.wraped = self.warp_image(corners)
                wraped_hsv = cv2.cvtColor(self.wraped, cv2.COLOR_BGR2HSV)
                hsv_blue = self.hsv_filter(wraped_hsv, "blue")
                # The cenrtor points of the blue dots
                self.centor_pts = self.find_centers(hsv_blue)
                for pt in self.centor_pts:
                    cv2.circle(self.wraped, pt, 2, (255, 255, 255), -1)
                self.centor_pts = np.array(self.centor_pts)
                middle_pts = np.mean(self.centor_pts, axis=0)
                self.middle_pts = self.match_centers(middle_pts, self.centor_pts)
                for pt in self.ref_pts:
                    h, w = self.wraped.shape[:2]
                    ratio_w = self.width / w
                    ratio_h = self.height / h
                    pt_img = pt/np.array([ratio_w, ratio_h]) + self.middle_pts
                    pt_img = pt_img.squeeze().astype(int)
                    cv2.circle(self.wraped, tuple(pt_img), 2, (0, 0, 255), -1)
                
                self.cal_error()
                for count, error in enumerate(self.error):
                    text_x = self.centor_pts[count][0] - 50
                    text_y = self.centor_pts[count][1] + 10
                    cv2.putText(self.wraped, str(round(error, 2)), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                
                cwd = os.getcwd()
                cv2.destroyAllWindows()
                cv2.imshow("hsv_blue", self.wraped)
                cv2.imwrite(cwd+"/imgs/error_result.png", self.wraped)
                cv2.waitKey(0)

def main():
    image = cv2.imread("imgs/test_color.png")
    cali = calibrator(image)
    cv2.imshow("image", cali.img)
    cv2.setMouseCallback('image', cali.click_event)
    cv2.waitKey(0)
    # cv2.destroyAllWindows()

if __name__ == "__main__":
    main()