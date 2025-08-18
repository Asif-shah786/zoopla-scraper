#!/usr/bin/env python3
"""
Real Estate Data Pipeline
=========================

Orchestrates the complete real estate data processing pipeline:
1. Scrape properties using zoopla_bulk_scraper.py
2. Integrate crime data using uk_police_api.py
3. Preprocess and clean data using data_preprocessing.py
4. Save all artifacts in organized run folders with logging

Each run creates a new folder: runs/run_X/ containing:
- scraped_data.json (raw scraped properties)
- properties_with_crime.json (properties + crime data)
- run_ready.json (final cleaned data for RAG)
- run_log.txt (detailed execution log)
"""

import os
import json
import shutil
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import traceback


class RealEstateDataPipeline:
    """Main pipeline class that orchestrates the entire real estate data processing workflow."""

    def __init__(self, base_output_dir: str = "runs"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

        # Get next run number
        self.run_number = self._get_next_run_number()
        self.run_dir = self.base_output_dir / f"run_{self.run_number}"
        self.run_dir.mkdir(exist_ok=True)

        # Initialize logging
        self.log_file = self.run_dir / "run_log.txt"
        self.start_time = datetime.now()

        # Run status tracking
        self.run_status = {
            "scraping": {
                "status": "pending",
                "start": None,
                "end": None,
                "error": None,
            },
            "crime_data": {
                "status": "pending",
                "start": None,
                "end": None,
                "error": None,
            },
            "preprocessing": {
                "status": "pending",
                "start": None,
                "end": None,
                "error": None,
            },
        }

        self.log(f"🚀 Starting Zoopla Scraper Engine - Run #{self.run_number}")
        self.log(f"📁 Run directory: {self.run_dir}")
        self.log(f"⏰ Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def _get_next_run_number(self) -> int:
        """Get the next available run number."""
        existing_runs = [
            d
            for d in self.base_output_dir.iterdir()
            if d.is_dir() and d.name.startswith("run_")
        ]

        if not existing_runs:
            return 1

        run_numbers = []
        for run_dir in existing_runs:
            try:
                num = int(run_dir.name.split("_")[1])
                run_numbers.append(num)
            except (ValueError, IndexError):
                continue

        return max(run_numbers) + 1 if run_numbers else 1

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message to both console and log file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"

        print(log_entry)

        # Append to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log error message with optional exception details."""
        error_msg = f"❌ ERROR: {message}"
        if error:
            error_msg += f"\n{traceback.format_exc()}"

        self.log(error_msg, "ERROR")

    def log_step_start(self, step: str) -> None:
        """Log the start of a pipeline step."""
        self.log(f"🔄 Starting {step}...")
        self.run_status[step]["start"] = datetime.now()
        self.run_status[step]["status"] = "running"

    def log_step_complete(
        self, step: str, success: bool = True, error: Optional[str] = None
    ) -> None:
        """Log the completion of a pipeline step."""
        self.run_status[step]["end"] = datetime.now()

        if success:
            duration = self.run_status[step]["end"] - self.run_status[step]["start"]
            self.log(
                f"✅ {step} completed successfully in {duration.total_seconds():.1f}s"
            )
            self.run_status[step]["status"] = "completed"
        else:
            error_msg = error if error else "Unknown error"
            self.log(f"❌ {step} failed: {error_msg}")
            self.run_status[step]["status"] = "failed"
            self.run_status[step]["error"] = error_msg

    async def run_scraping_step(self) -> Tuple[bool, str]:
        """Run the scraping step using zoopla_bulk_scraper.py."""
        self.log_step_start("scraping")

        try:
            # Check if zoopla_bulk_scraper.py exists
            scraper_file = "zoopla_bulk_scraper.py"
            if not os.path.exists(scraper_file):
                raise FileNotFoundError(f"Scraper file not found: {scraper_file}")

            self.log(f"📡 Running scraper: {scraper_file}")

            # Run the scraper as a subprocess and wait for completion
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                scraper_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = f"Scraper failed with return code {process.returncode}"
                if stderr:
                    error_msg += f"\nStderr: {stderr.decode()}"
                raise RuntimeError(error_msg)

            # Wait a moment for file system to update
            await asyncio.sleep(2)

            # Look for the generated file (most recent JSON file)
            json_files = list(Path(".").glob("*.json"))
            if not json_files:
                raise FileNotFoundError("No JSON files generated by scraper")

            # Get the most recent JSON file (should be the scraped data)
            latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
            if latest_file is None:
                raise FileNotFoundError("Could not determine latest JSON file")

            # Copy to run directory
            scraped_file = self.run_dir / "scraped_data.json"
            shutil.copy2(latest_file, scraped_file)

            self.log(f"📁 Scraped data saved to: {scraped_file}")
            self.log(f"📊 File size: {scraped_file.stat().st_size / 1024:.1f} KB")

            # Log scraper output
            if stdout:
                self.log(f"📝 Scraper output: {stdout.decode()[:200]}...")

            self.log_step_complete("scraping", success=True)
            return True, str(scraped_file)

        except Exception as e:
            error_msg = f"Scraping step failed: {str(e)}"
            self.log_error(error_msg, e)
            self.log_step_complete("scraping", success=False, error=error_msg)
            return False, error_msg

    async def run_crime_data_step(self, scraped_file_path: str) -> Tuple[bool, str]:
        """Run the crime data integration step using uk_police_api.py."""
        self.log_step_start("crime_data")

        try:
            # Check if uk_police_api.py exists
            crime_api_file = "uk_police_api.py"
            if not os.path.exists(crime_api_file):
                raise FileNotFoundError(f"Crime API file not found: {crime_api_file}")

            self.log(f"🚔 Running crime data integration: {crime_api_file}")

            # Import the crime API module directly instead of running as subprocess
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "uk_police_api", crime_api_file
            )
            if spec is None:
                raise ImportError(f"Could not create module spec for {crime_api_file}")
            crime_api = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                raise ImportError(f"Module spec has no loader for {crime_api_file}")
            spec.loader.exec_module(crime_api)

            # Create a temporary modified version of the load_properties function that uses our scraped file
            def modified_load_properties(max_items: int = 10):
                props = []
                try:
                    import json

                    with open(scraped_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Extract only essential fields needed for crime data lookup
                    for p in data[:max_items]:
                        lat = p.get("lat") or p.get("latitude")
                        lng = p.get("lon") or p.get("longitude")

                        # Skip properties with missing coordinates
                        if lat is None or lng is None or lat == 0 or lng == 0:
                            continue

                        props.append(
                            {
                                "title": p.get("listing_title") or "",
                                "address": p.get("address_full")
                                or p.get("address")
                                or "",
                                "postcode": p.get("outcode") or p.get("postcode"),
                                "lat": float(lat) if lat is not None else 0.0,
                                "lng": float(lng) if lng is not None else 0.0,
                            }
                        )
                    return props
                except Exception as e:
                    self.log(f"Error loading properties: {e}")
                    return []

            # Store the original function and replace it temporarily
            original_load_properties = getattr(crime_api, "load_properties", None)
            setattr(crime_api, "load_properties", modified_load_properties)

            try:
                # Run the crime data generation (this will write data/property_crime_summaries.json)
                crime_api.run_property_crime_summaries(max_items=100)
            finally:
                # Restore the original function
                if original_load_properties:
                    setattr(crime_api, "load_properties", original_load_properties)

            # Merge crime summaries into scraped data and save in run folder
            import json

            summaries_path = Path("property_crime_summaries.json")
            if not summaries_path.exists():
                raise FileNotFoundError("Crime summaries file not generated")

            with open(scraped_file_path, "r", encoding="utf-8") as f:
                scraped = json.load(f)
            with open(summaries_path, "r", encoding="utf-8") as f:
                summaries = json.load(f)

            # Build lookup maps for matching
            def round_coord(v: Optional[float]) -> Optional[float]:
                if v is None:
                    return None
                try:
                    return round(float(v), 5)
                except Exception:
                    return None

            by_coords = {}
            for idx, prop in enumerate(scraped):
                lat = prop.get("lat") or prop.get("latitude")
                lng = prop.get("lon") or prop.get("longitude")
                rlat, rlng = round_coord(lat), round_coord(lng)
                if rlat is not None and rlng is not None:
                    by_coords[(rlat, rlng)] = idx

            by_addr = {}
            for idx, prop in enumerate(scraped):
                addr = (
                    (prop.get("address_full") or prop.get("address") or "")
                    .strip()
                    .lower()
                )
                if addr:
                    by_addr[addr] = idx

            # Embed crime data
            embedded_count = 0
            for c in summaries:
                clat = round_coord(c.get("lat"))
                clng = round_coord(c.get("lng"))
                target_idx = None
                if clat is not None and clng is not None:
                    target_idx = by_coords.get((clat, clng))
                if target_idx is None:
                    caddr = (c.get("address") or "").strip().lower()
                    if caddr:
                        target_idx = by_addr.get(caddr)

                if target_idx is not None:
                    scraped[target_idx]["crime_summary"] = c.get("summary")
                    scraped[target_idx]["crime_data"] = c.get("aggregate")
                    embedded_count += 1

            # Save merged file in run directory
            run_crime_file = self.run_dir / "properties_with_crime.json"
            with open(run_crime_file, "w", encoding="utf-8") as f:
                json.dump(scraped, f, indent=2, ensure_ascii=False)

            self.log(
                f"🚔 Crime data saved to: {run_crime_file} (embedded for {embedded_count} properties)"
            )
            self.log(f"📊 File size: {run_crime_file.stat().st_size / 1024:.1f} KB")

            self.log_step_complete("crime_data", success=True)
            return True, str(run_crime_file)

        except Exception as e:
            error_msg = f"Crime data step failed: {str(e)}"
            self.log_error(error_msg, e)
            self.log_step_complete("crime_data", success=False, error=error_msg)
            return False, error_msg

    async def run_preprocessing_step(
        self, crime_data_file_path: str
    ) -> Tuple[bool, str]:
        """Run the preprocessing step using data_preprocessing.py."""
        self.log_step_start("preprocessing")

        try:
            # Check if data_preprocessing.py exists
            preprocess_file = "data_preprocessing.py"
            if not os.path.exists(preprocess_file):
                raise FileNotFoundError(
                    f"Preprocessing file not found: {preprocess_file}"
                )

            self.log(f"🧹 Running data preprocessing: {preprocess_file}")

            # Import and run the preprocessing function
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "data_preprocessing", preprocess_file
            )
            if spec is None:
                raise ImportError(f"Could not create module spec for {preprocess_file}")
            data_preprocessing = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                raise ImportError(f"Module spec has no loader for {preprocess_file}")
            spec.loader.exec_module(data_preprocessing)

            # Run preprocessing with our crime data file
            df_cleaned = data_preprocessing.load_and_clean_data(
                json_file_path=crime_data_file_path, output_dir=str(self.run_dir)
            )

            # Look for the generated cleaned file
            cleaned_files = list(self.run_dir.glob("*_cleaned.json"))
            if not cleaned_files:
                raise FileNotFoundError("Cleaned data file not generated")

            # Get the most recent cleaned file
            latest_cleaned = max(cleaned_files, key=lambda x: x.stat().st_mtime)

            # Rename to our standard name
            final_file = self.run_dir / "run_ready.json"
            shutil.copy2(latest_cleaned, final_file)

            self.log(f"🧹 Final cleaned data saved to: {final_file}")
            self.log(f"📊 File size: {final_file.stat().st_size / 1024:.1f} KB")
            self.log(f"📊 Dataset shape: {df_cleaned.shape}")

            self.log_step_complete("preprocessing", success=True)
            return True, str(final_file)

        except Exception as e:
            error_msg = f"Preprocessing step failed: {str(e)}"
            self.log_error(error_msg, e)
            self.log_step_complete("preprocessing", success=False, error=error_msg)
            return False, error_msg

    def save_run_summary(self) -> None:
        """Save a summary of the run including status and timing."""
        end_time = datetime.now()
        total_duration = end_time - self.start_time

        # Create JSON-serializable version of run status
        serializable_status = {}
        for step, status in self.run_status.items():
            serializable_status[step] = {
                "status": status["status"],
                "start": status["start"].isoformat() if status["start"] else None,
                "end": status["end"].isoformat() if status["end"] else None,
                "error": status["error"],
            }

        summary = {
            "run_number": self.run_number,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration.total_seconds(),
            "run_directory": str(self.run_dir),
            "steps": serializable_status,
            "overall_status": (
                "completed"
                if all(
                    step["status"] == "completed" for step in self.run_status.values()
                )
                else "failed"
            ),
        }

        # Save summary to JSON
        summary_file = self.run_dir / "run_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Save summary to log
        self.log("📊 Run Summary:")
        self.log(f"   Total duration: {total_duration.total_seconds():.1f}s")
        self.log(f"   Overall status: {summary['overall_status']}")

        for step, status in self.run_status.items():
            if status["status"] == "completed":
                duration = status["end"] - status["start"]
                self.log(f"   ✅ {step}: {duration.total_seconds():.1f}s")
            else:
                self.log(f"   ❌ {step}: {status['error']}")

        self.log(f"📁 Run summary saved to: {summary_file}")

    async def run_pipeline(self) -> bool:
        """Run the complete pipeline."""
        self.log("🚀 Starting complete pipeline execution...")

        try:
            # Step 1: Scraping
            scraping_success, scraped_file = await self.run_scraping_step()
            if not scraping_success:
                self.log("❌ Pipeline failed at scraping step")
                return False

            # Step 2: Crime Data Integration
            crime_success, crime_file = await self.run_crime_data_step(scraped_file)
            if not crime_success:
                self.log("❌ Pipeline failed at crime data step")
                return False

            # Step 3: Preprocessing
            preprocess_success, final_file = await self.run_preprocessing_step(
                crime_file
            )
            if not preprocess_success:
                self.log("❌ Pipeline failed at preprocessing step")
                return False

            # All steps completed successfully
            self.log("🎉 Pipeline completed successfully!")
            self.log(f"📁 Final output file: {final_file}")

            return True

        except Exception as e:
            self.log_error("Pipeline execution failed", e)
            return False

        finally:
            # Always save run summary
            self.save_run_summary()

    def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        try:
            # Remove any temporary files created during the run
            temp_files = list(self.run_dir.glob("temp_*"))
            for temp_file in temp_files:
                temp_file.unlink()
                self.log(f"🧹 Cleaned up temporary file: {temp_file}")

            # Clean up any other temporary files that might have been created
            for temp_pattern in ["temp_*", "*.tmp"]:
                temp_files = list(self.run_dir.glob(temp_pattern))
                for temp_file in temp_files:
                    try:
                        temp_file.unlink()
                        self.log(f"🧹 Cleaned up temporary file: {temp_file}")
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"⚠️ Warning: Could not clean up temporary files: {e}")


async def main():
    """Main function to run the scraper engine."""
    try:
        # Create and run the engine
        engine = RealEstateDataPipeline()

        # Run the complete pipeline
        success = await engine.run_pipeline()

        # Cleanup
        engine.cleanup()

        if success:
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📁 Check run results in: {engine.run_dir}")
        else:
            print(f"\n❌ Pipeline failed. Check logs in: {engine.run_dir}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
