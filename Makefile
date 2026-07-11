.PHONY: assets validate preview

assets:
	python scripts/build_assets.py

validate:
	python scripts/validate_profile.py

preview:
	python scripts/build_preview.py
