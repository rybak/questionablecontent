# must be "source"d

if test ! -d "$SRC"
then
	echo "Could not find source '$SRC'"
	echo "Make sure BOT_LOCATION='$BOT_LOCATION' has correct value"
	exit 1
fi
if test ! -d "$DEST"
then
	echo "Could not find destination '$DEST'"
	echo "Make sure BOT_LOCATION='$BOT_LOCATION' has correct value"
	exit 1
fi

NEW="$SRC/$filename"
OLD="$DEST/$filename"
if git diff --no-index "$OLD" "$NEW"
then
	echo "No difference from '$OLD' to '$NEW'"
	exit 1
fi

echo "Press Enter to apply these changes."
echo "Press Ctrl+C to abort."
read && cp "$NEW" "$OLD"

