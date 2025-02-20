#!/usr/bin/env python3

import os
import cv2
import time
import argparse
import numpy as np
from controllers.vision import VisionController

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                        required=True)
    parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                        default='detect.tflite')
    parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                        default='labelmap.txt')
    parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                        default=0.5)
    parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                        default='1280x720')
    parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                        action='store_true')
    args = parser.parse_args()
    
    # Get model paths
    model_path = os.path.join(args.modeldir, args.graph)
    label_path = os.path.join(args.modeldir, args.labels)
    
    # Parse resolution
    width, height = args.resolution.split('x')
    resolution = (int(width), int(height))
    
    # Initialize vision controller
    vision = VisionController(
        model_path=model_path,
        label_path=label_path,
        resolution=resolution,
        min_confidence=float(args.threshold),
        use_tpu=args.edgetpu,
        debug=True
    )
    
    # Create display window
    cv2.namedWindow('Object detector', cv2.WINDOW_NORMAL)
    
    def frame_callback(frame, detections):
        # Draw detections
        for i, (x, y, w, h) in enumerate(detections):
            # Get detection info
            object_name = vision.current_objects[i]
            score = vision.current_scores[i]
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (10, 255, 0), 2)
            
            # Draw label
            label = f'{object_name}: {int(score*100)}%'
            labelSize, baseLine = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            label_y = max(y, labelSize[1] + 10)
            cv2.rectangle(
                frame,
                (x, label_y - labelSize[1] - 10),
                (x + labelSize[0], label_y + baseLine - 10),
                (255, 255, 255),
                cv2.FILLED
            )
            cv2.putText(
                frame,
                label,
                (x, label_y - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2
            )
            
        # Draw FPS
        cv2.putText(
            frame,
            f'FPS: {vision.current_fps:.2f}',
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            2,
            cv2.LINE_AA
        )
            
        # Show frame
        cv2.imshow('Object detector', frame)
    
    # Register callback and start vision
    vision.add_frame_callback(frame_callback)
    vision.start()
    
    try:
        print('Press q to quit...')
        while True:
            if cv2.waitKey(1) == ord('q'):
                break
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print('Interrupted by user')
        
    finally:
        # Clean up
        vision.cleanup()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
