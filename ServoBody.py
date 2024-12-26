from I2CController import I2CController

class ServoBody:

  ARM_1_FULL_DOWN_PULSE = 1700
  ARM_1_FULL_UP_PULSE = 2800

  ARM_2_FULL_DOWN_PULSE = 2100
  ARM_2_FULL_UP_PULSE = 900

  TILT_HORIZONTAL_PULSE = 1600
  TILT_FULL_DOWN_PULSE = 1900
  TILT_FULL_UP_PULSE = 1100

  PAN_CENTER_PULSE = 1400
  PAN_FULL_RIGHT_PULSE = 700
  PAN_FULL_LEFT_PULSE = 2500

  def __init__(self):

    self.controller = I2CController(0x40, debug=False)
    self.controller.setPWMFreq(50)
    
    # self.control_car()
  def move_head(self, axis, value):
      if(axis == 'x'):
          pan_pulse = self.PAN_CENTER_PULSE - (value * 900)
          self.controller.Set_Pulse(5,pan_pulse)
      else:
          if(value > 0):
              tilt_pulse = self.TILT_HORIZONTAL_PULSE + (value * (self.TILT_FULL_DOWN_PULSE - self.TILT_HORIZONTAL_PULSE))
          else:
              tilt_pulse = self.TILT_HORIZONTAL_PULSE + (value * (self.TILT_HORIZONTAL_PULSE - self.TILT_FULL_UP_PULSE))

          self.controller.Set_Pulse(2,tilt_pulse)

  def move_arm(self, side, value):
      if(side == 'left'):
          arm_1_pulse = self.ARM_1_FULL_DOWN_PULSE + value * (self.ARM_1_FULL_UP_PULSE - self.ARM_1_FULL_DOWN_PULSE)
          # arm_1_pulse = self.ARM_1_FULL_DOWN_PULSE
          self.controller.Set_Pulse(7,arm_1_pulse)
      elif(side == 'right'):
          arm_2_pulse = self.ARM_2_FULL_DOWN_PULSE + value * (self.ARM_2_FULL_UP_PULSE - self.ARM_2_FULL_DOWN_PULSE)
          # arm_2_pulse = self.ARM_2_FULL_DOWN_PULSE
          self.controller.Set_Pulse(8,arm_2_pulse)