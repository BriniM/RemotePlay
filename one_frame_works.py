# Import Python's built-in asyncio module for running asynchronous tasks.
import asyncio

# Import Python's built-in threading module so the asyncio event loop
# can run in a separate background thread.
import threading

# Import the time module for delays and measuring elapsed time.
import time

# Import Path for easier and safer filesystem path handling.
from pathlib import Path

# Import datetime so we can put the current date and time into filenames.
from datetime import datetime

# Import RPDevice from pyremoteplay.
# RPDevice represents the PS5 Remote Play device.
from pyremoteplay import RPDevice

# Import QueueReceiver.
# QueueReceiver receives and stores video frames coming from Remote Play.
from pyremoteplay.receiver import QueueReceiver


# IP address of the PS5 on the local network.
POSTE_3 = "192.168.0.166"
POSTE_4 = "192.168.0.105"

# Directory where captured screenshots will be saved.
OUTPUT_DIR = Path("ps5_frames")

# Number of seconds between screenshots.
# 60 seconds means one screenshot every minute.
CAPTURE_INTERVAL = 60


# Define a function for retrieving the newest video frame.
def get_latest_frame(receiver):

    # Try to use QueueReceiver's get_latest_video_frame() method.
    try:

        # Return the newest frame currently available.
        return receiver.get_latest_video_frame()

    # Some versions of pyremoteplay may not have
    # get_latest_video_frame(), so catch AttributeError.
    except AttributeError:

        # Try the alternative video_frames interface.
        try:

            # Get the collection of received video frames.
            frames = receiver.video_frames

            # Check whether there is at least one frame.
            if frames:

                # Return the most recent frame.
                return frames[-1]

        # If anything goes wrong while accessing video_frames,
        # simply ignore the error and return None below.
        except Exception:

            # Do nothing here.
            pass

    # Return None when no frame is currently available.
    return None


# Define the main function containing the Remote Play program.
def main():

    # Print a title when the program starts.
    print("=== PS5 Remote Play Continuous Frame Capture ===")

    # Create the screenshot directory if it does not already exist.
    # parents=True also creates missing parent directories.
    # exist_ok=True prevents an error if the directory already exists.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create a pyremoteplay device object using the PS5's IP address.
    device = RPDevice(POSTE_3)

    # ---------------------------------------------------------
    # 1. Check whether the PS5 is reachable
    # ---------------------------------------------------------

    # Print a message so we know what the program is doing.
    print("\nGetting PS5 status...")

    # Ask the PS5 for its current Remote Play status.
    status = device.get_status()

    # Print the returned status information.
    print(status)

    # Check whether we received a valid response
    # and whether the returned HTTP-like status code is 200.
    if not status or status.get("status-code") != 200:

        # Tell the user that communication with the PS5 failed.
        print("Could not communicate with the PS5.")

        # Stop the program because we cannot continue.
        return

    # ---------------------------------------------------------
    # 2. Get the users registered on the PS5
    # ---------------------------------------------------------

    # Ask the PS5 for its registered users.
    users = device.get_users()

    # Print a heading for the list of users.
    print("\nRegistered users:")

    # Print the users returned by the PS5.
    print(users)

    # Check whether the PS5 returned an empty user list.
    if not users:

        # Explain why a user is required.
        print(
            "\nNo registered users found."
            "\nThe PSN account must first be registered with this PS5."
        )

        # Stop the program because a Remote Play session
        # cannot be created without a user.
        return

    # Select the first registered user.
    user = users[0]

    # Display which user will be used for the Remote Play session.
    print(f"\nUsing user: {user}")

    # ---------------------------------------------------------
    # 3. Create the Remote Play session
    # ---------------------------------------------------------

    # Create a QueueReceiver object.
    # This object will receive the video frames from the PS5.
    receiver = QueueReceiver()

    # Tell the user that the Remote Play session is being created.
    print("\nCreating Remote Play session...")

    # Create the Remote Play session.
    device.create_session(

        # Specify which PS5 user should be used.
        user,

        # Tell pyremoteplay where incoming video frames should go.
        receiver=receiver,

        # Request a 720p Remote Play video stream.
        resolution="720p",

        # Request 30 frames per second.
        fps=30,

        # Use the default Remote Play quality settings.
        quality="default",

        # Use H.264 for video decoding.
        codec="h264",
    )

    # Tell the user that the session was successfully created.
    print("Session created.")

    # ---------------------------------------------------------
    # 4. Create an asyncio event loop
    # ---------------------------------------------------------

    # Create a new asyncio event loop.
    # pyremoteplay needs this loop for its asynchronous networking.
    loop = asyncio.new_event_loop()

    # Define the function that will run the asyncio event loop.
    def run_loop():

        # Associate our newly created event loop
        # with this background thread.
        asyncio.set_event_loop(loop)

        # Keep the event loop running continuously.
        loop.run_forever()

    # Create a background thread.
    # The thread will run the asyncio event loop.
    thread = threading.Thread(

        # Tell the thread to execute the run_loop function.
        target=run_loop,

        # Make the thread a daemon thread.
        # This means it will not prevent Python from exiting.
        daemon=True,
    )

    # Start the background thread.
    thread.start()

    # ---------------------------------------------------------
    # 5. Connect to the PS5
    # ---------------------------------------------------------

    # Tell the user that we are connecting.
    print("\nConnecting to Remote Play...")

    # Schedule device.connect() to run inside the asyncio event loop.
    #
    # run_coroutine_threadsafe() is used because the event loop
    # is running in another thread.
    future = asyncio.run_coroutine_threadsafe(

        # Start the asynchronous Remote Play connection.
        device.connect(),

        # Specify which asyncio loop should execute it.
        loop,
    )

    # Try to wait for the connection to complete.
    try:

        # Wait up to 15 seconds for the connection.
        future.result(timeout=15)

    # Catch any exception raised while connecting.
    except Exception as e:

        # Print a message indicating that connection failed.
        print("\nConnection failed:")

        # Print the actual exception.
        print(repr(e))

        # Tell the asyncio loop to stop safely.
        loop.call_soon_threadsafe(loop.stop)

        # Wait briefly for the background thread to finish.
        thread.join(timeout=2)

        # Stop the program because the PS5 connection failed.
        return

    # Tell the user that Remote Play is now connected.
    print("\nRemote Play connected!")

    # ---------------------------------------------------------
    # 6. Wait for the first video frame
    # ---------------------------------------------------------

    # Tell the user that we are waiting for video.
    print("\nWaiting for first video frame...")

    # Start with no frame.
    frame = None

    # Continue checking until a frame becomes available.
    while frame is None:

        # Ask the receiver for the latest available frame.
        frame = get_latest_frame(receiver)

        # If there is still no frame,
        # wait 100 milliseconds before checking again.
        if frame is None:

            # Sleep for 0.1 seconds.
            time.sleep(0.1)

    # Tell the user that video has started arriving.
    print("\nFirst frame received!")

    # Print the width of the received video frame.
    print(f"Width:  {frame.width}")

    # Print the height of the received video frame.
    print(f"Height: {frame.height}")

    # Print the frame's pixel/image format.
    print(f"Format: {frame.format}")

    # ---------------------------------------------------------
    # 7. Start continuous screenshot capture
    # ---------------------------------------------------------

    # Tell the user that screenshots will now be captured continuously.
    print("\nStarting continuous capture.")

    # Display the configured screenshot interval.
    print(f"Saving one image every {CAPTURE_INTERVAL} seconds.")

    # Explain how the user can stop the program.
    print("Press CTRL+C to stop.\n")

    # Store the current monotonic clock value.
    #
    # time.monotonic() is preferable for measuring intervals because
    # it is not affected if the computer's system clock changes.
    last_capture = time.monotonic()

    # Run the capture loop until the user stops the program.
    try:

        # Keep the Remote Play connection alive indefinitely.
        while True:

            # Get the newest frame currently available.
            current_frame = get_latest_frame(receiver)

            # Check whether a new frame was successfully retrieved.
            if current_frame is not None:

                # Replace our stored frame with the newest frame.
                #
                # This means "frame" always represents approximately
                # the current PS5 screen.
                frame = current_frame

            # Get the current monotonic clock value.
            now = time.monotonic()

            # Check whether at least 60 seconds have passed
            # since the previous screenshot.
            if now - last_capture >= CAPTURE_INTERVAL:

                # Create a timestamp such as:
                # 2026-08-29_18-15-32
                timestamp = datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S"
                )

                # Construct the filename for this screenshot.
                #
                # Example:
                # ps5_frames/ps5_2026-08-29_18-15-32.png
                output_file = (
                    OUTPUT_DIR
                    / f"ps5_{timestamp}.png"
                )

                # Try to convert and save the frame.
                try:

                    # Convert the pyremoteplay video frame
                    # into a PIL/Pillow image.
                    image = frame.to_image()

                    # Save the image as a PNG file.
                    image.save(output_file)

                    # Print confirmation showing when and where
                    # the screenshot was saved.
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Saved: {output_file}"
                    )

                # Catch errors that occur during image conversion
                # or saving.
                except Exception as e:

                    # Print the time and error information.
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"Could not save frame: {repr(e)}"
                    )

                # Record the time of this screenshot.
                #
                # The next screenshot will occur approximately
                # 60 seconds after this point.
                last_capture = now

            # Sleep for 50 milliseconds before checking for another frame.
            #
            # The Remote Play stream continues independently in the
            # background, so we do not need to poll thousands of times
            # per second.
            time.sleep(0.05)

    # Catch CTRL+C from the keyboard.
    except KeyboardInterrupt:

        # Tell the user that capture is stopping.
        print("\n\nStopping capture...")

    # ---------------------------------------------------------
    # 8. Disconnect from Remote Play
    # ---------------------------------------------------------

    # Tell the user that we are disconnecting.
    print("Disconnecting from Remote Play...")

    # Try to disconnect the Remote Play session cleanly.
    try:

        # Disconnect from the PS5.
        device.disconnect()

    # Catch any error during disconnection.
    except Exception as e:

        # Print the disconnection error instead of crashing.
        print(f"Disconnect error: {repr(e)}")

    # Try to stop the asyncio event loop and background thread.
    try:

        # Ask the asyncio event loop to stop.
        #
        # call_soon_threadsafe() is necessary because the loop
        # is running inside another thread.
        loop.call_soon_threadsafe(loop.stop)

        # Wait up to two seconds for the thread to terminate.
        thread.join(timeout=2)

    # Ignore cleanup errors so the program can exit normally.
    except Exception:

        # Nothing needs to be done if cleanup fails.
        pass

    # Tell the user that the program has finished.
    print("Done.")


# Check whether this Python file is being executed directly.
if __name__ == "__main__":

    # Start the main program.
    main()
