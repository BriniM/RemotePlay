from pyremoteplay import RPDevice, oauth, profile

PS5_IP = "192.168.0.118"


def main():
    print("=== PS5 Remote Play Registration ===\n")

    # ---------------------------------------------------------
    # STEP 1: PSN OAuth login
    # ---------------------------------------------------------
    print("1. Open this URL in your browser:\n")

    login_url = oauth.get_login_url()
    print(login_url)

    print(
        "\nLog into the PSN account that is currently logged into "
        "the PS5."
    )

    print(
        "\nAfter logging in, you should be redirected to a page "
        "containing the redirect information."
    )

    redirect_url = input(
        "\nPaste the COMPLETE redirect URL here:\n> "
    ).strip()

    if not redirect_url:
        print("No redirect URL supplied.")
        return

    # Get PSN account information
    print("\nRetrieving PSN account information...")

    account = oauth.get_user_account(redirect_url)

    # Convert it into a pyremoteplay UserProfile
    user_profile = profile.format_user_account(account)
    print("\nPSN account:")
    print(user_profile)

    # ---------------------------------------------------------
    # STEP 2: Save the PSN profile
    # ---------------------------------------------------------
    profiles = RPDevice.get_profiles()

    profiles.update_user(user_profile)
    profiles.save()

    print("\nPSN profile saved.")

    # ---------------------------------------------------------
    # STEP 3: Connect to the PS5
    # ---------------------------------------------------------
    print(f"\nConnecting to PS5 at {PS5_IP}...")

    device = RPDevice(PS5_IP)

    status = device.get_status()

    print("\nPS5 status:")
    print(status)

    if not status:
        print("\nCould not retrieve PS5 status.")
        return

    # ---------------------------------------------------------
    # STEP 4: Get the Remote Play PIN
    # ---------------------------------------------------------
    print(
        "\nOn the PS5 go to:\n"
        "Settings → System → Remote Play → Link Device"
    )

    pin = input(
        "\nEnter the PIN displayed by the PS5:\n> "
    ).strip()

    if not pin:
        print("No PIN supplied.")
        return

    # ---------------------------------------------------------
    # STEP 5: Register PSN account with this PS5
    # ---------------------------------------------------------
    print("\nRegistering PSN account with PS5...")

    registered_profile = device.register(
        user_profile.name,
        pin,
        save=True
    )

    print("\nRegistration successful!")
    print("Registered profile:")
    print(registered_profile)

    # ---------------------------------------------------------
    # STEP 6: Verify
    # ---------------------------------------------------------
    users = device.get_users()

    print("\nRegistered users on this PS5:")
    print(users)

    if users:
        print("\nSUCCESS.")
        print("You can now create a Remote Play session using:")
        print(f"    device.create_session('{users[0]}')")
    else:
        print("\nRegistration completed, but no users were returned.")


if __name__ == "__main__":
    main()

