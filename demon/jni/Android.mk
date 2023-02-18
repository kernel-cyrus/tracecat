include $(CLEAR_VARS)
LOCAL_PATH 	:= .
LOCAL_MODULE    := tracecatd
LOCAL_SRC_FILES := includes/llist.c tracecatd.c
include $(BUILD_EXECUTABLE)